"""
Stock Screener 테스트
"""
import pytest
import pandas as pd
from stock_screener import StockScreener


class TestStockScreener:
    """StockScreener 테스트 클래스"""

    def test_screener_initialization(self):
        """스크리너 초기화 테스트"""
        screener = StockScreener()
        assert screener.df_krx is None

    @pytest.fixture
    def sample_ticker_data(self):
        """테스트용 샘플 종목 데이터"""
        return pd.DataFrame([
            {'Code': '005930', 'Name': '삼성전자', 'Market': 'KOSPI'},
            {'Code': '000660', 'Name': 'SK하이닉스', 'Market': 'KOSPI'},
            {'Code': '005935', 'Name': '삼성전자우', 'Market': 'KOSPI'},  # 우선주
            {'Code': '068270', 'Name': '셀트리온', 'Market': 'KOSPI'},
            {'Code': '123456', 'Name': '대한스팩1호', 'Market': 'KOSDAQ'},  # SPAC
            {'Code': '234567', 'Name': 'TIGER 200 ETF', 'Market': 'KOSPI'},  # ETF
            {'Code': '345678', 'Name': 'KB스타리츠', 'Market': 'KOSPI'},  # 리츠
            {'Code': '456789', 'Name': '카카오', 'Market': 'KOSDAQ'},
            {'Code': '567890', 'Name': '에스제이제1호스팩', 'Market': 'KOSDAQ'},  # SPAC
            {'Code': '678901', 'Name': 'KODEX 레버리지', 'Market': 'KOSPI'},  # ETF
        ])

    def test_apply_basic_filters(self, sample_ticker_data):
        """기본 필터링 테스트"""
        screener = StockScreener()
        screener.df_krx = sample_ticker_data

        # 필터링 실행
        result = screener.apply_basic_filters()

        # 검증
        assert len(result) == 4  # 삼성전자, SK하이닉스, 셀트리온, 카카오만 남음
        assert '005930' in result['Code'].values  # 삼성전자
        assert '000660' in result['Code'].values  # SK하이닉스
        assert '068270' in result['Code'].values  # 셀트리온
        assert '456789' in result['Code'].values  # 카카오

        # 제외된 종목 확인
        assert '005935' not in result['Code'].values  # 우선주
        assert '123456' not in result['Code'].values  # SPAC
        assert '234567' not in result['Code'].values  # ETF
        assert '345678' not in result['Code'].values  # 리츠

    def test_apply_basic_filters_removes_preferred_stocks(self, sample_ticker_data):
        """우선주 제외 테스트"""
        screener = StockScreener()
        screener.df_krx = sample_ticker_data

        result = screener.apply_basic_filters()

        # 우선주 제외 확인
        preferred_stocks = result[result['Name'].str.contains('우', na=False)]
        assert len(preferred_stocks) == 0

    def test_apply_basic_filters_removes_spac(self, sample_ticker_data):
        """SPAC 제외 테스트"""
        screener = StockScreener()
        screener.df_krx = sample_ticker_data

        result = screener.apply_basic_filters()

        # SPAC 제외 확인
        spac_stocks = result[result['Name'].str.contains('스팩', na=False)]
        assert len(spac_stocks) == 0

        spac_stocks_numbered = result[result['Name'].str.contains('제[0-9]+호', na=False, regex=True)]
        assert len(spac_stocks_numbered) == 0

    def test_apply_basic_filters_removes_etf(self, sample_ticker_data):
        """ETF/ETN 제외 테스트"""
        screener = StockScreener()
        screener.df_krx = sample_ticker_data

        result = screener.apply_basic_filters()

        # ETF/ETN 제외 확인
        etf_stocks = result[result['Name'].str.contains('ETF|ETN', na=False, case=False)]
        assert len(etf_stocks) == 0

    def test_apply_basic_filters_removes_reit(self, sample_ticker_data):
        """리츠/펀드 제외 테스트"""
        screener = StockScreener()
        screener.df_krx = sample_ticker_data

        result = screener.apply_basic_filters()

        # 리츠 제외 확인
        reit_stocks = result[result['Name'].str.contains('리츠|REIT|펀드', na=False, case=False)]
        assert len(reit_stocks) == 0

    def test_apply_basic_filters_with_custom_dataframe(self):
        """커스텀 데이터프레임으로 필터링 테스트"""
        screener = StockScreener()

        custom_df = pd.DataFrame([
            {'Code': '005930', 'Name': '삼성전자', 'Market': 'KOSPI'},
            {'Code': '005935', 'Name': '삼성전자우', 'Market': 'KOSPI'},
        ])

        result = screener.apply_basic_filters(df=custom_df)

        assert len(result) == 1
        assert result.iloc[0]['Code'] == '005930'

    def test_apply_basic_filters_empty_dataframe(self):
        """빈 데이터프레임 필터링 테스트"""
        screener = StockScreener()
        screener.df_krx = pd.DataFrame(columns=['Code', 'Name', 'Market'])

        result = screener.apply_basic_filters()

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_apply_basic_filters_all_filtered_out(self):
        """모든 종목이 필터링되는 경우 테스트"""
        screener = StockScreener()

        all_filtered_df = pd.DataFrame([
            {'Code': '005935', 'Name': '삼성전자우', 'Market': 'KOSPI'},
            {'Code': '123456', 'Name': '대한스팩1호', 'Market': 'KOSDAQ'},
            {'Code': '234567', 'Name': 'TIGER 200 ETF', 'Market': 'KOSPI'},
        ])

        screener.df_krx = all_filtered_df
        result = screener.apply_basic_filters()

        assert len(result) == 0

    def test_apply_basic_filters_preserves_columns(self, sample_ticker_data):
        """필터링 후 컬럼 보존 테스트"""
        screener = StockScreener()
        screener.df_krx = sample_ticker_data

        result = screener.apply_basic_filters()

        # 컬럼이 보존되는지 확인
        assert 'Code' in result.columns
        assert 'Name' in result.columns
        assert 'Market' in result.columns

    def test_apply_basic_filters_case_insensitive(self):
        """대소문자 무관 필터링 테스트"""
        screener = StockScreener()

        df = pd.DataFrame([
            {'Code': '111111', 'Name': 'KODEX etf', 'Market': 'KOSPI'},  # 소문자
            {'Code': '222222', 'Name': 'tiger ETF', 'Market': 'KOSPI'},  # 대문자
            {'Code': '333333', 'Name': 'KB리츠', 'Market': 'KOSPI'},
            {'Code': '444444', 'Name': 'NH REIT', 'Market': 'KOSPI'},  # 영문 대문자
        ])

        screener.df_krx = df
        result = screener.apply_basic_filters()

        # 모두 필터링되어야 함
        assert len(result) == 0

    def test_screen_method_integration(self, mocker):
        """screen 메서드 통합 테스트"""
        screener = StockScreener()

        # get_all_tickers 모킹
        sample_data = pd.DataFrame([
            {'Code': '005930', 'Name': '삼성전자', 'Market': 'KOSPI'},
            {'Code': '005935', 'Name': '삼성전자우', 'Market': 'KOSPI'},
            {'Code': '000660', 'Name': 'SK하이닉스', 'Market': 'KOSPI'},
        ])

        mocker.patch.object(screener, 'get_all_tickers', return_value=sample_data)

        # screen 메서드가 있다면 테스트
        if hasattr(screener, 'screen'):
            result = screener.screen()

            # 우선주가 제외되어야 함
            assert len(result) == 2
            assert '005935' not in result['Code'].values
