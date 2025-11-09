"""
Full F-Score 계산기 테스트
"""
import pytest
from full_fscore import FullFScoreCalculator


class TestFullFScoreCalculator:
    """FullFScoreCalculator 테스트 클래스"""

    def test_calculator_initialization_with_api_key(self):
        """API 키로 초기화 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')
        assert calculator.stock_code == '005930'
        assert calculator.dart_client is not None
        assert calculator.lite_calculator is not None

    def test_calculator_initialization_with_client(self, mock_opendart_client):
        """기존 클라이언트로 초기화 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_client=mock_opendart_client)
        assert calculator.stock_code == '005930'
        assert calculator.dart_client is mock_opendart_client

    def test_calculate_perfect_score(self, mocker, sample_financial_data):
        """완벽한 9점 계산 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 모킹 (6점 만점)
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

        mocker.patch.object(
            calculator.lite_calculator.fa,
            'get_data_lst_by',
            side_effect=mock_get_data
        )

        # OpenDart 데이터 모킹 (3점 만점)
        dart_data = {
            'operating_cf_current': 60_000_000_000,
            'operating_cf_previous': 55_000_000_000,
            'net_income_current': 50_000_000_000,
            'current_assets_current': 200_000_000_000,
            'current_assets_previous': 180_000_000_000,
            'current_liabilities_current': 100_000_000_000,
            'current_liabilities_previous': 95_000_000_000,
        }

        mocker.patch.object(
            calculator.dart_client,
            'get_all_fscore_data',
            return_value=dart_data
        )

        score, details = calculator.calculate(year='2024')

        # 검증
        assert score == 9  # 만점
        assert details['lite_score'] == 6
        assert details['additional_score'] == 3

        # Lite 항목
        assert details['net_income_positive'] is True
        assert details['roa_increasing'] is True
        assert details['debt_ratio_decreasing'] is True
        assert details['shares_not_increasing'] is True
        assert details['operating_margin_increasing'] is True
        assert details['asset_turnover_increasing'] is True

        # OpenDart 항목
        assert details['operating_cf_positive'] is True
        assert details['accrual'] is True  # OCF > 당기순이익
        assert details['current_ratio_increasing'] is True

    def test_calculate_with_negative_dart_data(self, mocker, sample_financial_data):
        """부정적인 OpenDart 데이터로 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 모킹 (6점)
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

        mocker.patch.object(
            calculator.lite_calculator.fa,
            'get_data_lst_by',
            side_effect=mock_get_data
        )

        # OpenDart 데이터 모킹 (0점 - 모두 부정적)
        dart_data = {
            'operating_cf_current': -10_000_000_000,  # 음수
            'operating_cf_previous': 5_000_000_000,
            'net_income_current': 50_000_000_000,  # OCF < 당기순이익
            'current_assets_current': 180_000_000_000,
            'current_assets_previous': 200_000_000_000,  # 감소
            'current_liabilities_current': 100_000_000_000,
            'current_liabilities_previous': 95_000_000_000,
        }

        mocker.patch.object(
            calculator.dart_client,
            'get_all_fscore_data',
            return_value=dart_data
        )

        score, details = calculator.calculate(year='2024')

        # 검증
        assert score == 6  # Lite만 점수
        assert details['lite_score'] == 6
        assert details['additional_score'] == 0

        # OpenDart 항목 - 모두 False
        assert details['operating_cf_positive'] is False
        assert details['accrual'] is False
        assert details['current_ratio_increasing'] is False

    def test_calculate_with_partial_dart_data(self, mocker, sample_financial_data):
        """부분적인 OpenDart 데이터 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 모킹 (6점)
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

        mocker.patch.object(
            calculator.lite_calculator.fa,
            'get_data_lst_by',
            side_effect=mock_get_data
        )

        # OpenDart 데이터 모킹 (일부만 있음)
        dart_data = {
            'operating_cf_current': 60_000_000_000,
            'operating_cf_previous': None,
            'net_income_current': 50_000_000_000,
            'current_assets_current': None,
            'current_assets_previous': None,
            'current_liabilities_current': None,
            'current_liabilities_previous': None,
        }

        mocker.patch.object(
            calculator.dart_client,
            'get_all_fscore_data',
            return_value=dart_data
        )

        score, details = calculator.calculate(year='2024')

        # 검증
        assert score == 8  # Lite 6 + OCF 2개
        assert details['lite_score'] == 6
        assert details['additional_score'] == 2

        # OpenDart 항목
        assert details['operating_cf_positive'] is True
        assert details['accrual'] is True
        assert details['current_ratio_increasing'] is None  # 데이터 없음

    def test_calculate_with_no_dart_data(self, mocker, sample_financial_data):
        """OpenDart 데이터 없이 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 모킹 (6점)
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

        mocker.patch.object(
            calculator.lite_calculator.fa,
            'get_data_lst_by',
            side_effect=mock_get_data
        )

        # OpenDart 데이터 없음
        mocker.patch.object(
            calculator.dart_client,
            'get_all_fscore_data',
            return_value=None
        )

        score, details = calculator.calculate(year='2024')

        # 검증
        assert score == 6  # Lite만
        assert details['lite_score'] == 6
        assert details['additional_score'] == 0

    def test_calculate_with_lite_failure(self, mocker):
        """Lite F-Score 실패 시 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 실패하도록 모킹
        mocker.patch.object(
            calculator.lite_calculator,
            'calculate',
            return_value=(None, None)
        )

        score, details = calculator.calculate(year='2024')

        # 검증
        assert score is None
        assert details is None

    def test_calculate_with_zero_current_liabilities(self, mocker, sample_financial_data):
        """유동부채가 0인 경우 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 모킹 (6점)
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

        mocker.patch.object(
            calculator.lite_calculator.fa,
            'get_data_lst_by',
            side_effect=mock_get_data
        )

        # OpenDart 데이터 - 유동부채 0
        dart_data = {
            'operating_cf_current': 60_000_000_000,
            'operating_cf_previous': 55_000_000_000,
            'net_income_current': 50_000_000_000,
            'current_assets_current': 200_000_000_000,
            'current_assets_previous': 180_000_000_000,
            'current_liabilities_current': 0,  # 0
            'current_liabilities_previous': 95_000_000_000,
        }

        mocker.patch.object(
            calculator.dart_client,
            'get_all_fscore_data',
            return_value=dart_data
        )

        score, details = calculator.calculate(year='2024')

        # 검증
        assert score == 8  # Lite 6 + OCF 2
        assert details['additional_score'] == 2
        assert details['current_ratio_increasing'] is None  # 계산 불가

    def test_calculate_uses_default_year(self, mocker, sample_financial_data):
        """연도 미지정 시 전년도 사용 테스트"""
        calculator = FullFScoreCalculator('005930', opendart_api_key='test_key')

        # Lite F-Score 모킹
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

        mocker.patch.object(
            calculator.lite_calculator.fa,
            'get_data_lst_by',
            side_effect=mock_get_data
        )

        # OpenDart 모킹
        mock_get_all = mocker.patch.object(
            calculator.dart_client,
            'get_all_fscore_data',
            return_value={}
        )

        calculator.calculate()  # year 미지정

        # get_all_fscore_data가 전년도로 호출되었는지 확인
        from datetime import datetime
        expected_year = str(datetime.now().year - 1)
        mock_get_all.assert_called_once_with('005930', expected_year)
