"""
Lite F-Score 계산기 테스트
"""
import pytest
from lite_fscore import LiteFScoreCalculator


class TestLiteFScoreCalculator:
    """LiteFScoreCalculator 테스트 클래스"""

    def test_calculator_initialization(self):
        """계산기 초기화 테스트"""
        calculator = LiteFScoreCalculator('005930')
        assert calculator.ticker == '005930'
        assert calculator.score == 0
        assert calculator.details == {}
        assert calculator.last_error is None

    def test_validate_data_with_valid_input(self):
        """유효한 데이터 검증 테스트"""
        calculator = LiteFScoreCalculator('005930')
        data_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        assert calculator._validate_data(data_list) is True

    def test_validate_data_with_none(self):
        """None 데이터 검증 테스트"""
        calculator = LiteFScoreCalculator('005930')
        data_list = [[1, 2, 3], None, [7, 8, 9]]
        assert calculator._validate_data(data_list) is False

    def test_validate_data_with_empty_list(self):
        """빈 리스트 데이터 검증 테스트"""
        calculator = LiteFScoreCalculator('005930')
        data_list = [[1, 2, 3], [], [7, 8, 9]]
        assert calculator._validate_data(data_list) is False

    def test_check_net_income_positive_when_positive(self):
        """당기순이익 > 0 테스트 (양수)"""
        calculator = LiteFScoreCalculator('005930')
        net_income = [100_000_000, 120_000_000, 150_000_000]
        calculator._check_net_income_positive(net_income)

        assert calculator.score == 1
        assert calculator.details['net_income_positive'] is True

    def test_check_net_income_positive_when_negative(self):
        """당기순이익 > 0 테스트 (음수)"""
        calculator = LiteFScoreCalculator('005930')
        net_income = [100_000_000, 80_000_000, -50_000_000]
        calculator._check_net_income_positive(net_income)

        assert calculator.score == 0
        assert calculator.details['net_income_positive'] is False

    def test_check_roa_increasing_when_increasing(self):
        """ROA 증가 테스트 (증가)"""
        calculator = LiteFScoreCalculator('005930')
        net_income = [100_000_000, 120_000_000]
        total_assets = [1_000_000_000, 1_100_000_000]
        calculator._check_roa_increasing(net_income, total_assets)

        assert calculator.score == 1
        assert calculator.details['roa_increasing'] is True
        assert calculator.details['roa_current'] == 10.91  # 120/1100 * 100
        assert calculator.details['roa_previous'] == 10.0  # 100/1000 * 100

    def test_check_roa_increasing_when_decreasing(self):
        """ROA 증가 테스트 (감소)"""
        calculator = LiteFScoreCalculator('005930')
        net_income = [100_000_000, 80_000_000]
        total_assets = [1_000_000_000, 1_100_000_000]
        calculator._check_roa_increasing(net_income, total_assets)

        assert calculator.score == 0
        assert calculator.details['roa_increasing'] is False
        assert calculator.details['roa_current'] < calculator.details['roa_previous']

    def test_check_debt_ratio_decreasing_when_decreasing(self):
        """부채비율 감소 테스트 (감소)"""
        calculator = LiteFScoreCalculator('005930')
        total_debt = [500_000_000, 480_000_000]
        total_assets = [1_000_000_000, 1_100_000_000]
        calculator._check_debt_ratio_decreasing(total_debt, total_assets)

        assert calculator.score == 1
        assert calculator.details['debt_ratio_decreasing'] is True
        assert calculator.details['debt_ratio_current'] == 43.64  # 480/1100 * 100
        assert calculator.details['debt_ratio_previous'] == 50.0  # 500/1000 * 100

    def test_check_debt_ratio_decreasing_when_increasing(self):
        """부채비율 감소 테스트 (증가)"""
        calculator = LiteFScoreCalculator('005930')
        total_debt = [500_000_000, 580_000_000]
        total_assets = [1_000_000_000, 1_100_000_000]
        calculator._check_debt_ratio_decreasing(total_debt, total_assets)

        assert calculator.score == 0
        assert calculator.details['debt_ratio_decreasing'] is False

    def test_check_shares_not_increasing_when_constant(self):
        """발행주식수 불변/감소 테스트 (불변)"""
        calculator = LiteFScoreCalculator('005930')
        shares = [10_000_000, 10_000_000]
        calculator._check_shares_not_increasing(shares)

        assert calculator.score == 1
        assert calculator.details['shares_not_increasing'] is True
        assert calculator.details['shares_current'] == 10_000_000
        assert calculator.details['shares_previous'] == 10_000_000

    def test_check_shares_not_increasing_when_decreasing(self):
        """발행주식수 불변/감소 테스트 (감소 - 자사주 매입)"""
        calculator = LiteFScoreCalculator('005930')
        shares = [10_000_000, 9_500_000]
        calculator._check_shares_not_increasing(shares)

        assert calculator.score == 1
        assert calculator.details['shares_not_increasing'] is True

    def test_check_shares_not_increasing_when_increasing(self):
        """발행주식수 불변/감소 테스트 (증가 - 희석)"""
        calculator = LiteFScoreCalculator('005930')
        shares = [10_000_000, 12_000_000]
        calculator._check_shares_not_increasing(shares)

        assert calculator.score == 0
        assert calculator.details['shares_not_increasing'] is False

    def test_check_operating_margin_increasing_when_increasing(self):
        """영업이익률 증가 테스트 (증가)"""
        calculator = LiteFScoreCalculator('005930')
        operating_income = [80_000_000, 95_000_000]
        revenue = [500_000_000, 550_000_000]
        calculator._check_operating_margin_increasing(operating_income, revenue)

        assert calculator.score == 1
        assert calculator.details['operating_margin_increasing'] is True
        assert calculator.details['operating_margin_current'] == 17.27  # 95/550 * 100
        assert calculator.details['operating_margin_previous'] == 16.0  # 80/500 * 100

    def test_check_operating_margin_increasing_when_decreasing(self):
        """영업이익률 증가 테스트 (감소)"""
        calculator = LiteFScoreCalculator('005930')
        operating_income = [80_000_000, 70_000_000]
        revenue = [500_000_000, 550_000_000]
        calculator._check_operating_margin_increasing(operating_income, revenue)

        assert calculator.score == 0
        assert calculator.details['operating_margin_increasing'] is False

    def test_check_asset_turnover_increasing_when_increasing(self):
        """자산회전율 증가 테스트 (증가)"""
        calculator = LiteFScoreCalculator('005930')
        revenue = [500_000_000, 600_000_000]
        total_assets = [1_000_000_000, 1_100_000_000]
        calculator._check_asset_turnover_increasing(revenue, total_assets)

        assert calculator.score == 1
        assert calculator.details['asset_turnover_increasing'] is True
        assert calculator.details['asset_turnover_current'] == 0.55  # 600/1100
        assert calculator.details['asset_turnover_previous'] == 0.5  # 500/1000

    def test_check_asset_turnover_increasing_when_decreasing(self):
        """자산회전율 증가 테스트 (감소)"""
        calculator = LiteFScoreCalculator('005930')
        revenue = [500_000_000, 450_000_000]
        total_assets = [1_000_000_000, 1_100_000_000]
        calculator._check_asset_turnover_increasing(revenue, total_assets)

        assert calculator.score == 0
        assert calculator.details['asset_turnover_increasing'] is False

    def test_get_score_interpretation(self):
        """점수 해석 테스트"""
        calculator = LiteFScoreCalculator('005930')

        calculator.score = None
        assert calculator.get_score_interpretation() == "데이터 부족"

        calculator.score = 6
        assert calculator.get_score_interpretation() == "우수 (Strong Buy)"

        calculator.score = 5
        assert calculator.get_score_interpretation() == "우수 (Strong Buy)"

        calculator.score = 4
        assert calculator.get_score_interpretation() == "양호 (Buy)"

        calculator.score = 3
        assert calculator.get_score_interpretation() == "보통 (Hold)"

        calculator.score = 2
        assert calculator.get_score_interpretation() == "주의 (Watch)"

        calculator.score = 1
        assert calculator.get_score_interpretation() == "부진 (Avoid)"

        calculator.score = 0
        assert calculator.get_score_interpretation() == "부진 (Avoid)"

    def test_calculate_with_mocked_data_perfect_score(self, mocker, sample_financial_data):
        """모킹된 데이터로 완벽한 점수 계산 테스트"""
        calculator = LiteFScoreCalculator('005930')

        # FundamentalAnalysis의 get_data_lst_by 메서드 모킹
        def mock_get_data(period, field):
            field_mapping = {
                '당기순이익': sample_financial_data['net_income'],
                '자산총계': sample_financial_data['total_assets'],
                '부채총계': sample_financial_data['total_debt'],
                '발행주식수': sample_financial_data['shares'],
                '매출액': sample_financial_data['revenue'],
                '영업이익': sample_financial_data['operating_income'],
            }
            return field_mapping.get(field, [])

        mocker.patch.object(calculator.fa, 'get_data_lst_by', side_effect=mock_get_data)

        score, details = calculator.calculate()

        assert score == 6  # 만점
        assert details['net_income_positive'] is True
        assert details['roa_increasing'] is True
        assert details['debt_ratio_decreasing'] is True
        assert details['shares_not_increasing'] is True
        assert details['operating_margin_increasing'] is True
        assert details['asset_turnover_increasing'] is True

    def test_calculate_with_mocked_data_zero_score(self, mocker, sample_negative_data):
        """모킹된 데이터로 최저 점수 계산 테스트"""
        calculator = LiteFScoreCalculator('005930')

        # FundamentalAnalysis의 get_data_lst_by 메서드 모킹
        def mock_get_data(period, field):
            field_mapping = {
                '당기순이익': sample_negative_data['net_income'],
                '자산총계': sample_negative_data['total_assets'],
                '부채총계': sample_negative_data['total_debt'],
                '발행주식수': sample_negative_data['shares'],
                '매출액': sample_negative_data['revenue'],
                '영업이익': sample_negative_data['operating_income'],
            }
            return field_mapping.get(field, [])

        mocker.patch.object(calculator.fa, 'get_data_lst_by', side_effect=mock_get_data)

        score, details = calculator.calculate()

        assert score == 0  # 0점
        assert details['net_income_positive'] is False
        assert details['roa_increasing'] is False
        assert details['debt_ratio_decreasing'] is False
        assert details['shares_not_increasing'] is False
        assert details['operating_margin_increasing'] is False
        assert details['asset_turnover_increasing'] is False

    def test_calculate_with_incomplete_data(self, mocker, sample_incomplete_data):
        """불완전한 데이터로 계산 실패 테스트"""
        calculator = LiteFScoreCalculator('005930')

        # FundamentalAnalysis의 get_data_lst_by 메서드 모킹
        def mock_get_data(period, field):
            field_mapping = {
                '당기순이익': sample_incomplete_data['net_income'],
                '자산총계': sample_incomplete_data['total_assets'],
                '부채총계': sample_incomplete_data['total_debt'],
                '발행주식수': sample_incomplete_data['shares'],
                '매출액': sample_incomplete_data['revenue'],
                '영업이익': sample_incomplete_data['operating_income'],
            }
            return field_mapping.get(field, [])

        mocker.patch.object(calculator.fa, 'get_data_lst_by', side_effect=mock_get_data)

        score, details = calculator.calculate()

        assert score is None
        assert details is None
        assert calculator.last_error is not None

    def test_calculate_with_insufficient_years(self, mocker):
        """최소 연도 데이터 부족 테스트"""
        calculator = LiteFScoreCalculator('005930')

        # 1년치 데이터만 제공
        def mock_get_data(period, field):
            return [100_000_000]  # 1년치만

        mocker.patch.object(calculator.fa, 'get_data_lst_by', side_effect=mock_get_data)

        score, details = calculator.calculate()

        assert score is None
        assert details is None
        assert calculator.last_error == "연속 연도 데이터 부족"

    def test_calculate_with_exception(self, mocker):
        """예외 발생 테스트"""
        calculator = LiteFScoreCalculator('005930')

        # 예외 발생하도록 모킹
        mocker.patch.object(
            calculator.fa,
            'get_data_lst_by',
            side_effect=Exception("API Error")
        )

        score, details = calculator.calculate()

        assert score is None
        assert details is None
        assert "예외 발생" in calculator.last_error
