"""
시가총액, 거래량, PER/PBR 등 시장 데이터 수집 모듈

pykrx와 FnGuide를 활용하여:
- 시가총액
- 현재 주가
- 거래량/거래대금
- PER, PBR
- 배당수익률
"""

import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import time


class MarketDataCollector:
    """시장 데이터 수집기"""

    def __init__(self):
        self.base_date = None  # 데이터 기준일

    def get_latest_trading_date(self):
        """
        가장 최근 거래일 찾기

        Returns:
        --------
        date : str
            최근 거래일 (YYYYMMDD)
        """
        # 오늘부터 최대 10일 전까지 거래일 탐색
        today = datetime.now()

        for i in range(10):
            check_date = (today - timedelta(days=i)).strftime('%Y%m%d')

            try:
                # 삼성전자로 거래일 확인
                df = stock.get_market_ohlcv_by_date(check_date, check_date, '005930')
                if len(df) > 0:
                    self.base_date = check_date
                    print(f"✅ 데이터 기준일: {check_date}")
                    return check_date
            except:
                continue

        # 못 찾으면 7일 전으로 설정 (주말 회피)
        fallback = (today - timedelta(days=7)).strftime('%Y%m%d')
        self.base_date = fallback
        return fallback

    def get_market_cap_info(self, code):
        """
        시가총액 정보 가져오기

        Parameters:
        -----------
        code : str
            종목 코드

        Returns:
        --------
        info : dict
            {
                'market_cap': 시가총액(억원),
                'market_cap_rank': 순위,
                'size_category': '대형주'/'중형주'/'소형주',
                'price': 현재가,
                'volume': 거래량,
                'trading_value': 거래대금(백만원)
            }
        """
        try:
            if not self.base_date:
                self.get_latest_trading_date()

            # 시가총액 조회
            df_cap = stock.get_market_cap_by_date(
                self.base_date,
                self.base_date,
                code
            )

            if len(df_cap) == 0:
                return None

            # 시가총액 (억원 단위)
            market_cap = df_cap.iloc[-1]['시가총액'] / 100_000_000

            # 주가 정보
            df_ohlcv = stock.get_market_ohlcv_by_date(
                self.base_date,
                self.base_date,
                code
            )

            if len(df_ohlcv) == 0:
                return None

            price = df_ohlcv.iloc[-1]['종가']
            volume = df_ohlcv.iloc[-1]['거래량']
            trading_value = df_ohlcv.iloc[-1]['거래대금'] / 1_000_000  # 백만원

            # 크기 분류
            if market_cap >= 10000:  # 1조원 이상
                size_category = '대형주'
            elif market_cap >= 1000:  # 1000억 이상
                size_category = '중형주'
            else:
                size_category = '소형주'

            return {
                'market_cap': round(market_cap, 0),
                'size_category': size_category,
                'price': int(price),
                'volume': int(volume),
                'trading_value': round(trading_value, 0)
            }

        except Exception as e:
            return None

    def get_valuation_from_fnguide(self, code):
        """
        FnGuide에서 PER, PBR, 배당수익률 가져오기

        Parameters:
        -----------
        code : str
            종목 코드

        Returns:
        --------
        valuation : dict
            {
                'per': PER,
                'pbr': PBR,
                'div_yield': 배당수익률(%)
            }
        """
        try:
            url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A{code}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # PER, PBR, 배당수익률 추출
            result = {
                'per': None,
                'pbr': None,
                'div_yield': None
            }

            # 주요 투자지표 테이블에서 추출
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')

                    if th and td:
                        label = th.get_text(strip=True)
                        value_text = td.get_text(strip=True).replace(',', '')

                        try:
                            if 'PER' in label:
                                result['per'] = float(value_text)
                            elif 'PBR' in label:
                                result['pbr'] = float(value_text)
                            elif '배당수익률' in label:
                                result['div_yield'] = float(value_text)
                        except:
                            continue

            return result

        except Exception as e:
            return {
                'per': None,
                'pbr': None,
                'div_yield': None
            }

    def get_all_market_data(self, code):
        """
        모든 시장 데이터 통합 수집

        Parameters:
        -----------
        code : str
            종목 코드

        Returns:
        --------
        data : dict
            모든 시장 데이터 통합
        """
        result = {}

        # 1. 시가총액 및 거래 정보
        cap_info = self.get_market_cap_info(code)
        if cap_info:
            result.update(cap_info)

        # 2. 밸류에이션 정보
        valuation = self.get_valuation_from_fnguide(code)
        result.update(valuation)

        return result if len(result) > 0 else None

    def get_average_trading_value(self, code, days=20):
        """
        평균 거래대금 계산 (N일)

        Parameters:
        -----------
        code : str
            종목 코드
        days : int
            계산 기간 (기본 20일)

        Returns:
        --------
        avg_trading_value : float
            평균 거래대금 (백만원)
        """
        try:
            if not self.base_date:
                self.get_latest_trading_date()

            # N일 전 날짜
            end_date = datetime.strptime(self.base_date, '%Y%m%d')
            start_date = (end_date - timedelta(days=days+10)).strftime('%Y%m%d')  # 여유있게

            df = stock.get_market_ohlcv_by_date(start_date, self.base_date, code)

            if len(df) == 0:
                return None

            # 최근 N일 평균
            recent_df = df.tail(days)
            avg_value = recent_df['거래대금'].mean() / 1_000_000  # 백만원

            return round(avg_value, 0)

        except Exception as e:
            return None


def test_collector():
    """테스트 실행"""
    print("="*60)
    print("🧪 시장 데이터 수집 테스트")
    print("="*60)

    collector = MarketDataCollector()

    # 테스트 종목들
    test_stocks = [
        ('005930', '삼성전자'),
        ('207940', '삼성바이오로직스'),
        ('035720', '카카오'),
    ]

    for code, name in test_stocks:
        print(f"\n📊 {name} ({code})")

        data = collector.get_all_market_data(code)

        if data:
            print(f"  시가총액: {data.get('market_cap', 'N/A'):,}억원 ({data.get('size_category', 'N/A')})")
            print(f"  현재가: {data.get('price', 'N/A'):,}원")
            print(f"  거래량: {data.get('volume', 'N/A'):,}주")
            print(f"  거래대금: {data.get('trading_value', 'N/A'):,}백만원")
            print(f"  PER: {data.get('per', 'N/A')}")
            print(f"  PBR: {data.get('pbr', 'N/A')}")
            print(f"  배당수익률: {data.get('div_yield', 'N/A')}%")
        else:
            print("  ❌ 데이터 없음")

        time.sleep(1)  # API 과부하 방지

    print(f"\n{'='*60}")
    print("✅ 테스트 완료")


if __name__ == "__main__":
    test_collector()
