"""
pytest 설정 및 공통 fixtures
"""
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_financial_data():
    """테스트용 샘플 재무 데이터"""
    return {
        'net_income': [100_000_000, 120_000_000, 150_000_000],  # 증가 추세
        'total_assets': [1_000_000_000, 1_100_000_000, 1_200_000_000],
        'total_debt': [500_000_000, 480_000_000, 460_000_000],  # 감소 추세
        'shares': [10_000_000, 10_000_000, 10_000_000],  # 불변
        'revenue': [500_000_000, 550_000_000, 600_000_000],  # 증가
        'operating_income': [80_000_000, 95_000_000, 110_000_000],  # 증가
    }


@pytest.fixture
def sample_negative_data():
    """테스트용 부정적 재무 데이터"""
    return {
        'net_income': [100_000_000, 80_000_000, -50_000_000],  # 감소 & 적자
        'total_assets': [1_000_000_000, 1_100_000_000, 1_200_000_000],
        'total_debt': [500_000_000, 580_000_000, 660_000_000],  # 증가 추세
        'shares': [10_000_000, 12_000_000, 15_000_000],  # 증가 (희석)
        'revenue': [500_000_000, 480_000_000, 450_000_000],  # 감소
        'operating_income': [80_000_000, 70_000_000, 60_000_000],  # 감소
    }


@pytest.fixture
def sample_incomplete_data():
    """테스트용 불완전한 데이터"""
    return {
        'net_income': [100_000_000],  # 1년치만
        'total_assets': [],
        'total_debt': None,
        'shares': [10_000_000],
        'revenue': [],
        'operating_income': [80_000_000],
    }


@pytest.fixture
def sample_opendart_data():
    """테스트용 OpenDart API 응답 데이터"""
    return {
        'status': '000',
        'message': '정상',
        'list': [
            {
                'rcept_no': '20240101000001',
                'corp_code': '00126380',
                'corp_name': '삼성전자',
                'account_nm': '영업활동으로인한현금흐름',
                'thstrm_amount': '50000000000',
                'frmtrm_amount': '45000000000',
            },
            {
                'rcept_no': '20240101000001',
                'corp_code': '00126380',
                'corp_name': '삼성전자',
                'account_nm': '유동자산',
                'thstrm_amount': '200000000000',
                'frmtrm_amount': '180000000000',
            },
            {
                'rcept_no': '20240101000001',
                'corp_code': '00126380',
                'corp_name': '삼성전자',
                'account_nm': '유동부채',
                'thstrm_amount': '100000000000',
                'frmtrm_amount': '95000000000',
            },
        ]
    }


@pytest.fixture
def mock_opendart_client(mocker, sample_opendart_data):
    """모의 OpenDart 클라이언트"""
    from opendart_client import OpenDartClient

    client = OpenDartClient(api_key='test_api_key')

    # get_company_code 모킹
    mocker.patch.object(
        client,
        'get_company_code',
        return_value='00126380'
    )

    # get_financial_statements 모킹
    mocker.patch.object(
        client,
        'get_financial_statements',
        return_value=sample_opendart_data
    )

    # get_cashflow 모킹
    mocker.patch.object(
        client,
        'get_cashflow',
        return_value=50_000_000_000
    )

    # get_current_ratio 모킹
    mocker.patch.object(
        client,
        'get_current_ratio',
        return_value=(2.0, 1.9)  # 증가
    )

    return client
