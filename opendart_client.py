"""
OpenDart API 클라이언트

공식 재무제표 데이터 수집:
- 영업현금흐름
- 유동자산, 유동부채
- 더 정확한 재무 지표
"""

import requests
import pandas as pd
from datetime import datetime
import time


class OpenDartClient:
    """OpenDart API 클라이언트"""

    def __init__(self, api_key):
        """
        Parameters:
        -----------
        api_key : str
            OpenDart API 인증키
        """
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"

    def get_company_code(self, stock_code):
        """
        종목 코드 → 고유번호(corp_code) 변환

        Parameters:
        -----------
        stock_code : str
            6자리 종목 코드 (예: 005930)

        Returns:
        --------
        corp_code : str
            8자리 고유번호 또는 None
        """
        try:
            url = f"{self.base_url}/corpCode.xml"
            params = {'crtfc_key': self.api_key}

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                # XML에서 corp_code 찾기
                import zipfile
                import io
                import xml.etree.ElementTree as ET

                # ZIP 파일 압축 해제
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                xml_data = zip_file.read('CORPCODE.xml')

                # XML 파싱
                root = ET.fromstring(xml_data)

                for company in root.findall('list'):
                    code = company.find('stock_code').text
                    if code == stock_code:
                        corp_code = company.find('corp_code').text
                        return corp_code

            return None

        except Exception as e:
            print(f"  ⚠️  고유번호 조회 실패: {e}")
            return None

    def get_financial_statements(self, corp_code, year, report_code='11011', fs_div='CFS'):
        """
        재무제표 조회

        Parameters:
        -----------
        corp_code : str
            8자리 고유번호
        year : str
            사업연도 (YYYY)
        report_code : str
            보고서 코드
            - 11011: 사업보고서
            - 11012: 반기보고서
            - 11013: 1분기보고서
            - 11014: 3분기보고서
        fs_div : str
            재무제표 구분
            - CFS: 연결재무제표 (기본)
            - OFS: 개별재무제표

        Returns:
        --------
        df : DataFrame
            재무제표 데이터
        """
        try:
            url = f"{self.base_url}/fnlttSinglAcntAll.json"

            params = {
                'crtfc_key': self.api_key,
                'corp_code': corp_code,
                'bsns_year': year,
                'reprt_code': report_code,
                'fs_div': fs_div
            }

            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if data['status'] == '000':
                df = pd.DataFrame(data['list'])
                return df
            else:
                # 연결재무제표 없으면 개별재무제표 시도
                if fs_div == 'CFS':
                    return self.get_financial_statements(corp_code, year, report_code, 'OFS')
                return None

        except Exception as e:
            return None

    def get_cashflow_statement(self, corp_code, year):
        """
        현금흐름표 조회

        Parameters:
        -----------
        corp_code : str
            고유번호
        year : str
            사업연도

        Returns:
        --------
        operating_cashflow : dict
            {
                'current': 당기 영업현금흐름,
                'previous': 전기 영업현금흐름
            }
        """
        try:
            df = self.get_financial_statements(corp_code, year, '11011')

            if df is None or len(df) == 0:
                return None

            # 현금흐름표만 필터링
            df_cf = df[df['sj_div'] == 'CF'].copy()

            if len(df_cf) == 0:
                return None

            # 영업활동으로 인한 현금흐름 찾기
            keywords = ['영업활동으로인한현금흐름', '영업활동현금흐름', '영업활동으로 인한 현금흐름']

            for keyword in keywords:
                rows = df_cf[df_cf['account_nm'].str.replace(' ', '').str.contains(keyword, na=False)]

                if len(rows) > 0:
                    row = rows.iloc[0]

                    # 당기, 전기 값 추출
                    current = self._parse_number(row['thstrm_amount'])
                    previous = self._parse_number(row['frmtrm_amount'])

                    return {
                        'current': current,
                        'previous': previous
                    }

            return None

        except Exception as e:
            return None

    def get_current_ratio_data(self, corp_code, year):
        """
        유동비율 계산을 위한 데이터 조회

        Parameters:
        -----------
        corp_code : str
            고유번호
        year : str
            사업연도

        Returns:
        --------
        data : dict
            {
                'current_assets_current': 당기 유동자산,
                'current_assets_previous': 전기 유동자산,
                'current_liabilities_current': 당기 유동부채,
                'current_liabilities_previous': 전기 유동부채
            }
        """
        try:
            df = self.get_financial_statements(corp_code, year, '11011')

            if df is None or len(df) == 0:
                return None

            # 재무상태표만 필터링
            df_bs = df[df['sj_div'] == 'BS'].copy()

            if len(df_bs) == 0:
                return None

            result = {}

            # 유동자산 찾기
            current_assets = df_bs[df_bs['account_nm'].str.replace(' ', '') == '유동자산']
            if len(current_assets) > 0:
                row = current_assets.iloc[0]
                result['current_assets_current'] = self._parse_number(row['thstrm_amount'])
                result['current_assets_previous'] = self._parse_number(row['frmtrm_amount'])

            # 유동부채 찾기
            current_liabilities = df_bs[df_bs['account_nm'].str.replace(' ', '') == '유동부채']
            if len(current_liabilities) > 0:
                row = current_liabilities.iloc[0]
                result['current_liabilities_current'] = self._parse_number(row['thstrm_amount'])
                result['current_liabilities_previous'] = self._parse_number(row['frmtrm_amount'])

            return result if len(result) == 4 else None

        except Exception as e:
            return None

    def get_net_income(self, corp_code, year):
        """
        당기순이익 조회

        Parameters:
        -----------
        corp_code : str
            고유번호
        year : str
            사업연도

        Returns:
        --------
        net_income : dict
            {
                'current': 당기,
                'previous': 전기
            }
        """
        try:
            df = self.get_financial_statements(corp_code, year, '11011')

            if df is None or len(df) == 0:
                return None

            # 포괄손익계산서 필터링
            df_is = df[df['sj_div'] == 'IS'].copy()

            if len(df_is) == 0:
                return None

            # 당기순이익 찾기
            keywords = ['당기순이익', '당기순이익(손실)']

            for keyword in keywords:
                rows = df_is[df_is['account_nm'].str.replace(' ', '') == keyword.replace(' ', '')]

                if len(rows) > 0:
                    row = rows.iloc[0]

                    return {
                        'current': self._parse_number(row['thstrm_amount']),
                        'previous': self._parse_number(row['frmtrm_amount'])
                    }

            return None

        except Exception as e:
            return None

    def _parse_number(self, value_str):
        """
        숫자 문자열을 float로 변환

        Parameters:
        -----------
        value_str : str
            숫자 문자열 (예: "1,234,567")

        Returns:
        --------
        value : float
        """
        try:
            if pd.isna(value_str) or value_str == '' or value_str == '-':
                return None

            # 쉼표 제거 후 숫자 변환
            value = float(str(value_str).replace(',', ''))
            return value

        except:
            return None

    def get_all_fscore_data(self, stock_code, year=None):
        """
        F-Score에 필요한 모든 데이터 수집

        Parameters:
        -----------
        stock_code : str
            6자리 종목 코드
        year : str
            사업연도 (None이면 최근년도)

        Returns:
        --------
        data : dict
            F-Score 계산용 데이터
        """
        try:
            # 연도 설정
            if year is None:
                year = str(datetime.now().year - 1)  # 작년

            # 1. 고유번호 조회
            corp_code = self.get_company_code(stock_code)
            if not corp_code:
                return None

            # 2. 영업현금흐름
            cashflow = self.get_cashflow_statement(corp_code, year)

            # 3. 유동자산/부채
            current_ratio_data = self.get_current_ratio_data(corp_code, year)

            # 4. 당기순이익
            net_income = self.get_net_income(corp_code, year)

            # 통합
            result = {
                'stock_code': stock_code,
                'year': year,
                'corp_code': corp_code
            }

            if cashflow:
                result.update({
                    'operating_cf_current': cashflow['current'],
                    'operating_cf_previous': cashflow['previous']
                })

            if current_ratio_data:
                result.update(current_ratio_data)

            if net_income:
                result.update({
                    'net_income_current': net_income['current'],
                    'net_income_previous': net_income['previous']
                })

            return result

        except Exception as e:
            print(f"  ⚠️  데이터 수집 실패: {e}")
            return None


def test_client():
    """테스트 실행"""
    print("="*60)
    print("🧪 OpenDart API 테스트")
    print("="*60)

    api_key = "0893a49ad29a0b7fc3b47bf0a26fa580a1c10808"
    client = OpenDartClient(api_key)

    # 테스트 종목
    test_stocks = [
        ('005930', '삼성전자'),
        ('207940', '삼성바이오로직스'),
    ]

    for code, name in test_stocks:
        print(f"\n📊 {name} ({code})")

        data = client.get_all_fscore_data(code, '2023')

        if data:
            print(f"  ✅ 데이터 수집 성공")
            print(f"  고유번호: {data.get('corp_code')}")

            if data.get('operating_cf_current'):
                print(f"  영업현금흐름(당기): {data['operating_cf_current']:,.0f}")
            if data.get('operating_cf_previous'):
                print(f"  영업현금흐름(전기): {data['operating_cf_previous']:,.0f}")

            if data.get('current_assets_current'):
                print(f"  유동자산(당기): {data['current_assets_current']:,.0f}")
            if data.get('current_liabilities_current'):
                print(f"  유동부채(당기): {data['current_liabilities_current']:,.0f}")

            if data.get('net_income_current'):
                print(f"  당기순이익(당기): {data['net_income_current']:,.0f}")
        else:
            print("  ❌ 데이터 없음")

        time.sleep(2)  # API 과부하 방지

    print(f"\n{'='*60}")
    print("✅ 테스트 완료")


if __name__ == "__main__":
    test_client()
