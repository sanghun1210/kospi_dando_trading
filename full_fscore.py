"""
Full F-Score 계산기 (9/9 지표)

FnGuide + OpenDart 데이터를 통합하여 완전한 F-Score 계산
"""

from lite_fscore import LiteFScoreCalculator
from opendart_client import OpenDartClient
from datetime import datetime


class FullFScoreCalculator:
    """
    Full F-Score 계산기 (9/9 지표)

    Lite F-Score (6개) + OpenDart (3개)
    """

    def __init__(self, stock_code, opendart_api_key):
        """
        Parameters:
        -----------
        stock_code : str
            6자리 종목 코드
        opendart_api_key : str
            OpenDart API 인증키
        """
        self.stock_code = stock_code
        self.lite_calculator = LiteFScoreCalculator(stock_code)
        self.dart_client = OpenDartClient(opendart_api_key)

    def calculate(self, year=None):
        """
        Full F-Score 계산 (9/9)

        Parameters:
        -----------
        year : str
            사업연도 (None이면 전년도)

        Returns:
        --------
        score : int
            0~9점
        details : dict
            상세 항목별 결과
        """
        # 1. Lite F-Score 계산 (6개)
        lite_score, lite_details = self.lite_calculator.calculate()

        if lite_score is None:
            return None, None

        # 2. OpenDart 데이터 가져오기
        if year is None:
            year = str(datetime.now().year - 1)

        dart_data = self.dart_client.get_all_fscore_data(self.stock_code, year)

        # 3. 추가 3개 지표 계산
        additional_score = 0
        additional_details = {}

        if dart_data:
            # (7) 영업현금흐름 > 0
            operating_cf = dart_data.get('operating_cf_current')
            if operating_cf is not None:
                cf_positive = operating_cf > 0
                additional_details['operating_cf_positive'] = cf_positive
                additional_details['operating_cf'] = operating_cf
                if cf_positive:
                    additional_score += 1
            else:
                additional_details['operating_cf_positive'] = None
                additional_details['operating_cf'] = None

            # (8) 영업현금흐름 > 당기순이익 (회계 품질)
            net_income = dart_data.get('net_income_current')
            if operating_cf is not None and net_income is not None:
                accrual = operating_cf > net_income
                additional_details['accrual'] = accrual
                additional_details['net_income'] = net_income
                if accrual:
                    additional_score += 1
            else:
                additional_details['accrual'] = None
                additional_details['net_income'] = net_income

            # (9) 유동비율 증가
            ca_current = dart_data.get('current_assets_current')
            ca_previous = dart_data.get('current_assets_previous')
            cl_current = dart_data.get('current_liabilities_current')
            cl_previous = dart_data.get('current_liabilities_previous')

            if all([ca_current, ca_previous, cl_current, cl_previous]):
                if cl_current > 0 and cl_previous > 0:
                    current_ratio_now = ca_current / cl_current
                    current_ratio_prev = ca_previous / cl_previous
                    current_ratio_increasing = current_ratio_now > current_ratio_prev

                    additional_details['current_ratio_increasing'] = current_ratio_increasing
                    additional_details['current_ratio_current'] = round(current_ratio_now, 2)
                    additional_details['current_ratio_previous'] = round(current_ratio_prev, 2)

                    if current_ratio_increasing:
                        additional_score += 1
                else:
                    additional_details['current_ratio_increasing'] = None
            else:
                additional_details['current_ratio_increasing'] = None

        # 4. 통합
        full_score = lite_score + additional_score

        full_details = {**lite_details, **additional_details}
        full_details['lite_score'] = lite_score
        full_details['additional_score'] = additional_score

        return full_score, full_details

    def get_score_breakdown(self, details):
        """
        점수 분석 출력

        Parameters:
        -----------
        details : dict
            계산 결과 상세
        """
        print(f"\n{'='*60}")
        print(f"Full F-Score 분석: {self.stock_code}")
        print(f"{'='*60}")

        print(f"\n📊 Lite F-Score (6개 지표): {details.get('lite_score', 0)}/6")
        print(f"  1. 당기순이익 > 0: {'✅' if details.get('net_income_positive') else '❌'}")
        print(f"  2. ROA 증가: {'✅' if details.get('roa_increasing') else '❌'}")
        print(f"  3. 부채비율 감소: {'✅' if details.get('debt_ratio_decreasing') else '❌'}")
        print(f"  4. 발행주식수 불변/감소: {'✅' if details.get('shares_not_increasing') else '❌'}")
        print(f"  5. 영업이익률 증가: {'✅' if details.get('operating_margin_increasing') else '❌'}")
        print(f"  6. 자산회전율 증가: {'✅' if details.get('asset_turnover_increasing') else '❌'}")

        print(f"\n📈 OpenDart 추가 (3개 지표): {details.get('additional_score', 0)}/3")

        cf_positive = details.get('operating_cf_positive')
        if cf_positive is not None:
            status = '✅' if cf_positive else '❌'
            print(f"  7. 영업현금흐름 > 0: {status}")
            if details.get('operating_cf'):
                print(f"     ({details['operating_cf']:,.0f})")
        else:
            print(f"  7. 영업현금흐름 > 0: ⚠️  데이터 없음")

        accrual = details.get('accrual')
        if accrual is not None:
            status = '✅' if accrual else '❌'
            print(f"  8. 영업CF > 당기순이익: {status}")
            if details.get('operating_cf') and details.get('net_income'):
                print(f"     (CF: {details['operating_cf']:,.0f} vs 순이익: {details['net_income']:,.0f})")
        else:
            print(f"  8. 영업CF > 당기순이익: ⚠️  데이터 없음")

        cr_increasing = details.get('current_ratio_increasing')
        if cr_increasing is not None:
            status = '✅' if cr_increasing else '❌'
            print(f"  9. 유동비율 증가: {status}")
            if details.get('current_ratio_current'):
                print(f"     ({details['current_ratio_previous']} → {details['current_ratio_current']})")
        else:
            print(f"  9. 유동비율 증가: ⚠️  데이터 없음")

        print(f"\n{'='*60}")
        print(f"🎯 Total F-Score: {details.get('lite_score', 0) + details.get('additional_score', 0)}/9")
        print(f"{'='*60}\n")


def test_full_fscore():
    """테스트 실행"""
    print("="*60)
    print("🧪 Full F-Score 테스트")
    print("="*60)

    api_key = "0893a49ad29a0b7fc3b47bf0a26fa580a1c10808"

    test_stocks = [
        ('005930', '삼성전자'),
        ('207940', '삼성바이오로직스'),
    ]

    for code, name in test_stocks:
        print(f"\n{'='*60}")
        print(f"📊 {name} ({code})")
        print(f"{'='*60}")

        calculator = FullFScoreCalculator(code, api_key)
        score, details = calculator.calculate('2023')

        if score is not None:
            calculator.get_score_breakdown(details)
        else:
            print(f"  ❌ 계산 실패")

        import time
        time.sleep(2)  # API 과부하 방지

    print(f"\n{'='*60}")
    print("✅ 테스트 완료")


if __name__ == "__main__":
    test_full_fscore()
