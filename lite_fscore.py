"""
Lite F-Score 계산 모듈
FnGuide 데이터만으로 F-Score 일부 항목 계산 (6/9개)

원래 F-Score 9개 항목:
1. ✅ 당기순이익 > 0
2. ❌ 영업현금흐름 > 0 (OpenDart 필요)
3. ✅ ROA 증가
4. ❌ OCF > 당기순이익 (OpenDart 필요)
5. ✅ 부채비율 감소
6. ❌ 유동비율 증가 (데이터 없음)
7. ✅ 발행주식수 불변 or 감소
8. ✅ 매출총이익률 증가 (영업이익/매출액로 대체)
9. ✅ 자산회전율 증가

Lite F-Score: 6개 항목 (만점 6점)
OpenDart 연동 후 Full F-Score로 업그레이드 예정
"""

from fundametal_analysis import FundamentalAnalysis


class LiteFScoreCalculator:
    """Lite F-Score 계산기 (FnGuide 데이터 활용)"""

    def __init__(self, ticker):
        self.ticker = ticker
        self.fa = FundamentalAnalysis(ticker)
        self.score = 0
        self.details = {}
        self.last_error = None

    def calculate(self):
        """
        Lite F-Score 계산 (0-6점)

        Returns:
            score: int (0-6점)
            details: dict (각 항목별 결과)
        """
        try:
            self.last_error = None
            # 필요한 데이터 수집
            net_income = self.fa.get_data_lst_by("Annual", "당기순이익")
            total_assets = self.fa.get_data_lst_by("Annual", "자산총계")
            total_debt = self.fa.get_data_lst_by("Annual", "부채총계")
            shares = self.fa.get_data_lst_by("Annual", "발행주식수")
            revenue = self.fa.get_data_lst_by("Annual", "매출액")
            operating_income = self.fa.get_data_lst_by("Annual", "영업이익")

            # 데이터 검증
            if not self._validate_data([net_income, total_assets, total_debt,
                                       shares, revenue, operating_income]):
                self.last_error = "필수 재무 데이터 부족"
                return None, None

            # 최소 2년 데이터 필요
            if len(net_income) < 2:
                self.last_error = "연속 연도 데이터 부족"
                return None, None

            # 각 항목 계산
            self.score = 0
            self.details = {}

            # 1. 당기순이익 > 0
            self._check_net_income_positive(net_income)

            # 2. ROA 증가
            self._check_roa_increasing(net_income, total_assets)

            # 3. 부채비율 감소
            self._check_debt_ratio_decreasing(total_debt, total_assets)

            # 4. 발행주식수 불변 or 감소
            self._check_shares_not_increasing(shares)

            # 5. 영업이익률 증가 (매출총이익률 대체)
            self._check_operating_margin_increasing(operating_income, revenue)

            # 6. 자산회전율 증가
            self._check_asset_turnover_increasing(revenue, total_assets)

            return self.score, self.details

        except Exception as e:
            self.last_error = f"예외 발생: {e}"
            print(f"Error calculating Lite F-Score for {self.ticker}: {e}")
            return None, None

    def _validate_data(self, data_list):
        """데이터 유효성 검증"""
        for data in data_list:
            if data is None or len(data) == 0:
                return False
        return True

    def _check_net_income_positive(self, net_income):
        """1. 당기순이익 > 0"""
        try:
            if net_income[-1] > 0:
                self.score += 1
                self.details['net_income_positive'] = True
            else:
                self.details['net_income_positive'] = False
        except:
            self.details['net_income_positive'] = None

    def _check_roa_increasing(self, net_income, total_assets):
        """2. ROA 증가 (당기순이익/자산총계)"""
        try:
            roa_current = net_income[-1] / total_assets[-1]
            roa_previous = net_income[-2] / total_assets[-2]

            if roa_current > roa_previous:
                self.score += 1
                self.details['roa_increasing'] = True
            else:
                self.details['roa_increasing'] = False

            self.details['roa_current'] = round(roa_current * 100, 2)
            self.details['roa_previous'] = round(roa_previous * 100, 2)
        except:
            self.details['roa_increasing'] = None

    def _check_debt_ratio_decreasing(self, total_debt, total_assets):
        """3. 부채비율 감소"""
        try:
            # 부채비율 = 부채총계/자산총계
            debt_ratio_current = total_debt[-1] / total_assets[-1]
            debt_ratio_previous = total_debt[-2] / total_assets[-2]

            if debt_ratio_current < debt_ratio_previous:
                self.score += 1
                self.details['debt_ratio_decreasing'] = True
            else:
                self.details['debt_ratio_decreasing'] = False

            self.details['debt_ratio_current'] = round(debt_ratio_current * 100, 2)
            self.details['debt_ratio_previous'] = round(debt_ratio_previous * 100, 2)
        except:
            self.details['debt_ratio_decreasing'] = None

    def _check_shares_not_increasing(self, shares):
        """4. 발행주식수 불변 or 감소 (자사주 소각 등)"""
        try:
            shares_current = shares[-1]
            shares_previous = shares[-2]

            if shares_current <= shares_previous:
                self.score += 1
                self.details['shares_not_increasing'] = True
            else:
                self.details['shares_not_increasing'] = False

            self.details['shares_current'] = shares_current
            self.details['shares_previous'] = shares_previous
        except:
            self.details['shares_not_increasing'] = None

    def _check_operating_margin_increasing(self, operating_income, revenue):
        """5. 영업이익률 증가 (영업이익/매출액)"""
        try:
            margin_current = operating_income[-1] / revenue[-1]
            margin_previous = operating_income[-2] / revenue[-2]

            if margin_current > margin_previous:
                self.score += 1
                self.details['operating_margin_increasing'] = True
            else:
                self.details['operating_margin_increasing'] = False

            self.details['operating_margin_current'] = round(margin_current * 100, 2)
            self.details['operating_margin_previous'] = round(margin_previous * 100, 2)
        except:
            self.details['operating_margin_increasing'] = None

    def _check_asset_turnover_increasing(self, revenue, total_assets):
        """6. 자산회전율 증가 (매출액/자산총계)"""
        try:
            turnover_current = revenue[-1] / total_assets[-1]
            turnover_previous = revenue[-2] / total_assets[-2]

            if turnover_current > turnover_previous:
                self.score += 1
                self.details['asset_turnover_increasing'] = True
            else:
                self.details['asset_turnover_increasing'] = False

            self.details['asset_turnover_current'] = round(turnover_current, 2)
            self.details['asset_turnover_previous'] = round(turnover_previous, 2)
        except:
            self.details['asset_turnover_increasing'] = None

    def get_score_interpretation(self):
        """점수 해석"""
        if self.score is None:
            return "데이터 부족"
        elif self.score >= 5:
            return "우수 (Strong Buy)"
        elif self.score >= 4:
            return "양호 (Buy)"
        elif self.score >= 3:
            return "보통 (Hold)"
        elif self.score >= 2:
            return "주의 (Watch)"
        else:
            return "부진 (Avoid)"

    def print_details(self):
        """상세 결과 출력"""
        print(f"\n{'='*60}")
        print(f"Lite F-Score: {self.ticker}")
        print(f"{'='*60}")
        print(f"총점: {self.score}/6 - {self.get_score_interpretation()}")
        print(f"\n항목별 점수:")
        print(f"  1. 당기순이익 > 0: {'✅' if self.details.get('net_income_positive') else '❌'}")
        print(f"  2. ROA 증가: {'✅' if self.details.get('roa_increasing') else '❌'}")
        if self.details.get('roa_current'):
            print(f"     - 현재: {self.details['roa_current']}%, 전년: {self.details['roa_previous']}%")
        print(f"  3. 부채비율 감소: {'✅' if self.details.get('debt_ratio_decreasing') else '❌'}")
        if self.details.get('debt_ratio_current'):
            print(f"     - 현재: {self.details['debt_ratio_current']}%, 전년: {self.details['debt_ratio_previous']}%")
        print(f"  4. 발행주식수 불변/감소: {'✅' if self.details.get('shares_not_increasing') else '❌'}")
        print(f"  5. 영업이익률 증가: {'✅' if self.details.get('operating_margin_increasing') else '❌'}")
        if self.details.get('operating_margin_current'):
            print(f"     - 현재: {self.details['operating_margin_current']}%, 전년: {self.details['operating_margin_previous']}%")
        print(f"  6. 자산회전율 증가: {'✅' if self.details.get('asset_turnover_increasing') else '❌'}")
        if self.details.get('asset_turnover_current'):
            print(f"     - 현재: {self.details['asset_turnover_current']}, 전년: {self.details['asset_turnover_previous']}")
        print(f"{'='*60}\n")


def main():
    """테스트"""
    # 삼성전자로 테스트
    print("📊 Lite F-Score 계산 테스트\n")

    test_tickers = [
        ('005930', '삼성전자'),
        ('000660', 'SK하이닉스'),
        ('035720', '카카오'),
    ]

    for code, name in test_tickers:
        print(f"\n{'='*60}")
        print(f"종목: {name} ({code})")
        print(f"{'='*60}")

        calculator = LiteFScoreCalculator(code)
        score, details = calculator.calculate()

        if score is not None:
            calculator.print_details()
        else:
            print("❌ 데이터 부족으로 계산 불가\n")


if __name__ == "__main__":
    main()
