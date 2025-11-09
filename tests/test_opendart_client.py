"""
OpenDart API 클라이언트 테스트
"""
import pytest
from opendart_client import OpenDartClient
import pandas as pd


class TestOpenDartClient:
    """OpenDartClient 테스트 클래스"""

    def test_client_initialization(self):
        """클라이언트 초기화 테스트"""
        client = OpenDartClient(api_key='test_api_key')
        assert client.api_key == 'test_api_key'
        assert client.base_url == 'https://opendart.fss.or.kr/api'
        assert client._corp_code_cache is None

    def test_parse_number(self):
        """숫자 파싱 테스트"""
        client = OpenDartClient(api_key='test_key')

        # 정상 케이스
        assert client._parse_number('1234567890') == 1234567890
        assert client._parse_number('123.45') == 123.45

        # 빈 값
        assert client._parse_number('') == 0
        assert client._parse_number(None) == 0
        assert client._parse_number('-') == 0

        # 음수
        assert client._parse_number('-12345') == -12345

    def test_get_company_code_with_cache(self, mocker):
        """캐시된 종목 코드 조회 테스트"""
        client = OpenDartClient(api_key='test_key')

        # 캐시 직접 설정
        client._corp_code_cache = {
            '005930': '00126380',  # 삼성전자
            '000660': '00164779',  # SK하이닉스
        }

        # 테스트
        assert client.get_company_code('005930') == '00126380'
        assert client.get_company_code('000660') == '00164779'
        assert client.get_company_code('999999') is None

    def test_get_company_code_without_cache(self, mocker):
        """캐시 없이 종목 코드 조회 테스트"""
        client = OpenDartClient(api_key='test_key')

        # _load_corp_code_cache 모킹
        def mock_load_cache():
            client._corp_code_cache = {
                '005930': '00126380',
            }

        mocker.patch.object(client, '_load_corp_code_cache', side_effect=mock_load_cache)

        # 테스트
        assert client.get_company_code('005930') == '00126380'

    def test_get_financial_statements_success(self, mocker):
        """재무제표 조회 성공 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock 응답 데이터
        mock_response = {
            'status': '000',
            'message': '정상',
            'list': [
                {
                    'rcept_no': '20240101000001',
                    'sj_div': 'BS',
                    'account_nm': '유동자산',
                    'thstrm_amount': '100000000000',
                    'frmtrm_amount': '95000000000',
                }
            ]
        }

        # requests.get 모킹
        mock_get = mocker.patch('requests.get')
        mock_get.return_value.json.return_value = mock_response

        # 테스트
        df = client.get_financial_statements('00126380', '2024')

        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['account_nm'] == '유동자산'

    def test_get_financial_statements_fallback_to_ofs(self, mocker):
        """연결재무제표 실패 시 개별재무제표 조회 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock 응답 - CFS 실패, OFS 성공
        call_count = [0]

        def mock_json():
            call_count[0] += 1
            if call_count[0] == 1:
                # 첫 번째 호출 (CFS) - 실패
                return {'status': '013', 'message': '데이터 없음'}
            else:
                # 두 번째 호출 (OFS) - 성공
                return {
                    'status': '000',
                    'message': '정상',
                    'list': [{'account_nm': '유동자산'}]
                }

        mock_get = mocker.patch('requests.get')
        mock_get.return_value.json.side_effect = mock_json

        # 테스트
        df = client.get_financial_statements('00126380', '2024', fs_div='CFS')

        assert df is not None
        assert isinstance(df, pd.DataFrame)

    def test_get_financial_statements_failure(self, mocker):
        """재무제표 조회 실패 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock 응답 - 실패
        mock_get = mocker.patch('requests.get')
        mock_get.return_value.json.return_value = {
            'status': '013',
            'message': '데이터 없음'
        }

        # 테스트 - OFS도 실패
        df = client.get_financial_statements('00126380', '2024', fs_div='OFS')

        assert df is None

    def test_get_financial_statements_exception(self, mocker):
        """재무제표 조회 예외 처리 테스트"""
        client = OpenDartClient(api_key='test_key')

        # 예외 발생하도록 모킹
        mock_get = mocker.patch('requests.get')
        mock_get.side_effect = Exception('Network error')

        # 테스트
        df = client.get_financial_statements('00126380', '2024')

        assert df is None

    def test_get_cashflow_statement_success(self, mocker):
        """현금흐름표 조회 성공 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock 재무제표 데이터
        mock_df = pd.DataFrame([
            {
                'sj_div': 'CF',
                'account_nm': '영업활동으로인한현금흐름',
                'thstrm_amount': '50000000000',
                'frmtrm_amount': '45000000000',
            }
        ])

        mocker.patch.object(client, 'get_financial_statements', return_value=mock_df)

        # 테스트
        result = client.get_cashflow_statement('00126380', '2024')

        assert result is not None
        assert result['current'] == 50000000000
        assert result['previous'] == 45000000000

    def test_get_cashflow_statement_no_data(self, mocker):
        """현금흐름표 데이터 없음 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock - 빈 데이터
        mocker.patch.object(client, 'get_financial_statements', return_value=None)

        # 테스트
        result = client.get_cashflow_statement('00126380', '2024')

        assert result is None

    def test_get_cashflow_statement_no_cf_section(self, mocker):
        """현금흐름표 섹션 없음 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock - CF 섹션 없음
        mock_df = pd.DataFrame([
            {
                'sj_div': 'BS',  # 재무상태표만
                'account_nm': '유동자산',
                'thstrm_amount': '100000000000',
                'frmtrm_amount': '95000000000',
            }
        ])

        mocker.patch.object(client, 'get_financial_statements', return_value=mock_df)

        # 테스트
        result = client.get_cashflow_statement('00126380', '2024')

        assert result is None

    def test_get_current_ratio_data_success(self, mocker):
        """유동비율 데이터 조회 성공 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock 재무제표 데이터
        mock_df = pd.DataFrame([
            {
                'sj_div': 'BS',
                'account_nm': '유동자산',
                'thstrm_amount': '200000000000',
                'frmtrm_amount': '180000000000',
            },
            {
                'sj_div': 'BS',
                'account_nm': '유동부채',
                'thstrm_amount': '100000000000',
                'frmtrm_amount': '95000000000',
            }
        ])

        mocker.patch.object(client, 'get_financial_statements', return_value=mock_df)

        # 테스트
        result = client.get_current_ratio_data('00126380', '2024')

        assert result is not None
        assert result['current_assets_current'] == 200000000000
        assert result['current_assets_previous'] == 180000000000
        assert result['current_liabilities_current'] == 100000000000
        assert result['current_liabilities_previous'] == 95000000000

    def test_get_current_ratio_data_incomplete(self, mocker):
        """유동비율 데이터 불완전 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock - 유동자산만 있음
        mock_df = pd.DataFrame([
            {
                'sj_div': 'BS',
                'account_nm': '유동자산',
                'thstrm_amount': '200000000000',
                'frmtrm_amount': '180000000000',
            }
        ])

        mocker.patch.object(client, 'get_financial_statements', return_value=mock_df)

        # 테스트
        result = client.get_current_ratio_data('00126380', '2024')

        assert result is None  # 불완전한 데이터

    def test_get_net_income_success(self, mocker):
        """당기순이익 조회 성공 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock 재무제표 데이터
        mock_df = pd.DataFrame([
            {
                'sj_div': 'IS',
                'account_nm': '당기순이익',
                'thstrm_amount': '30000000000',
                'frmtrm_amount': '25000000000',
            }
        ])

        mocker.patch.object(client, 'get_financial_statements', return_value=mock_df)

        # 테스트
        result = client.get_net_income('00126380', '2024')

        assert result is not None
        assert result['current'] == 30000000000
        assert result['previous'] == 25000000000

    def test_get_all_fscore_data_success(self, mocker):
        """전체 F-Score 데이터 조회 성공 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock get_company_code
        mocker.patch.object(client, 'get_company_code', return_value='00126380')

        # Mock 각 메서드
        mocker.patch.object(client, 'get_cashflow_statement', return_value={
            'current': 50000000000,
            'previous': 45000000000
        })

        mocker.patch.object(client, 'get_current_ratio_data', return_value={
            'current_assets_current': 200000000000,
            'current_assets_previous': 180000000000,
            'current_liabilities_current': 100000000000,
            'current_liabilities_previous': 95000000000
        })

        mocker.patch.object(client, 'get_net_income', return_value={
            'current': 30000000000,
            'previous': 25000000000
        })

        # 테스트
        result = client.get_all_fscore_data('005930', '2024')

        assert result is not None
        assert result['operating_cf_current'] == 50000000000
        assert result['operating_cf_previous'] == 45000000000
        assert result['current_assets_current'] == 200000000000
        assert result['current_liabilities_current'] == 100000000000
        assert result['net_income_current'] == 30000000000

    def test_get_all_fscore_data_no_corp_code(self, mocker):
        """종목 코드 없을 때 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock get_company_code - None 반환
        mocker.patch.object(client, 'get_company_code', return_value=None)

        # 테스트
        result = client.get_all_fscore_data('999999', '2024')

        assert result is None

    def test_get_all_fscore_data_partial(self, mocker):
        """부분 데이터만 있을 때 테스트"""
        client = OpenDartClient(api_key='test_key')

        # Mock get_company_code
        mocker.patch.object(client, 'get_company_code', return_value='00126380')

        # Mock - 현금흐름만 성공
        mocker.patch.object(client, 'get_cashflow_statement', return_value={
            'current': 50000000000,
            'previous': 45000000000
        })

        # 나머지는 None
        mocker.patch.object(client, 'get_current_ratio_data', return_value=None)
        mocker.patch.object(client, 'get_net_income', return_value=None)

        # 테스트
        result = client.get_all_fscore_data('005930', '2024')

        assert result is not None
        assert result['operating_cf_current'] == 50000000000
        assert result['current_assets_current'] is None
        assert result['net_income_current'] is None
