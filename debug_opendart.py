"""
OpenDart API 실패 원인 분석
"""

from opendart_client import OpenDartClient
import pandas as pd
import time


def debug_opendart():
    """OpenDart 실패 원인 분석"""

    print("="*60)
    print("🔍 OpenDart 실패 원인 분석")
    print("="*60)

    api_key = "0893a49ad29a0b7fc3b47bf0a26fa580a1c10808"
    client = OpenDartClient(api_key)

    # 상위 50개 종목 로드
    df = pd.read_csv('df_sorted.csv', sep='\t', encoding='utf-8')
    # 종목 코드를 6자리 문자열로 변환 (zero-padding)
    df['Code'] = df['Code'].astype(str).str.zfill(6)
    test_stocks = df.head(50)[['Code', 'Name']].values.tolist()

    results = {
        'corp_code_success': 0,
        'corp_code_fail': 0,
        'financial_success': 0,
        'financial_fail': 0,
        'cashflow_success': 0,
        'cashflow_fail': 0,
        'current_ratio_success': 0,
        'current_ratio_fail': 0
    }

    fail_examples = []

    print(f"\n📊 {len(test_stocks)}개 종목 분석 중...\n")

    for i, (code, name) in enumerate(test_stocks, 1):
        if i % 10 == 0:
            print(f"  진행: {i}/{len(test_stocks)}")

        # 1. 고유번호 조회
        corp_code = client.get_company_code(code)
        if corp_code:
            results['corp_code_success'] += 1
        else:
            results['corp_code_fail'] += 1
            fail_examples.append({
                'code': code,
                'name': name,
                'fail_stage': '고유번호 조회 실패'
            })
            continue

        # 2. 재무제표 조회
        df_fs = client.get_financial_statements(corp_code, '2023', '11011')
        if df_fs is not None and len(df_fs) > 0:
            results['financial_success'] += 1
        else:
            results['financial_fail'] += 1
            fail_examples.append({
                'code': code,
                'name': name,
                'fail_stage': '재무제표 없음 (2023년)'
            })
            continue

        # 3. 현금흐름표 조회
        cashflow = client.get_cashflow_statement(corp_code, '2023')
        if cashflow:
            results['cashflow_success'] += 1
        else:
            results['cashflow_fail'] += 1
            fail_examples.append({
                'code': code,
                'name': name,
                'fail_stage': '현금흐름표 없음'
            })

        # 4. 유동비율 데이터 조회
        current_ratio = client.get_current_ratio_data(corp_code, '2023')
        if current_ratio:
            results['current_ratio_success'] += 1
        else:
            results['current_ratio_fail'] += 1
            if not any(f['code'] == code for f in fail_examples):
                fail_examples.append({
                    'code': code,
                    'name': name,
                    'fail_stage': '유동자산/부채 없음'
                })

        time.sleep(0.3)  # API 과부하 방지

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"📊 분석 결과")
    print(f"{'='*60}\n")

    total = len(test_stocks)

    print(f"1️⃣ 고유번호 조회:")
    print(f"   성공: {results['corp_code_success']}/{total} ({results['corp_code_success']/total*100:.1f}%)")
    print(f"   실패: {results['corp_code_fail']}/{total} ({results['corp_code_fail']/total*100:.1f}%)")

    print(f"\n2️⃣ 재무제표 조회 (2023년):")
    print(f"   성공: {results['financial_success']}/{total} ({results['financial_success']/total*100:.1f}%)")
    print(f"   실패: {results['financial_fail']}/{total} ({results['financial_fail']/total*100:.1f}%)")

    print(f"\n3️⃣ 현금흐름표 조회:")
    print(f"   성공: {results['cashflow_success']}/{total} ({results['cashflow_success']/total*100:.1f}%)")
    print(f"   실패: {results['cashflow_fail']}/{total} ({results['cashflow_fail']/total*100:.1f}%)")

    print(f"\n4️⃣ 유동비율 데이터 조회:")
    print(f"   성공: {results['current_ratio_success']}/{total} ({results['current_ratio_success']/total*100:.1f}%)")
    print(f"   실패: {results['current_ratio_fail']}/{total} ({results['current_ratio_fail']/total*100:.1f}%)")

    # 실패 사례
    print(f"\n{'='*60}")
    print(f"❌ 실패 사례 (상위 20개)")
    print(f"{'='*60}\n")

    for i, fail in enumerate(fail_examples[:20], 1):
        print(f"{i}. {fail['name']} ({fail['code']})")
        print(f"   → {fail['fail_stage']}")

    # 분석
    print(f"\n{'='*60}")
    print(f"💡 분석 결과")
    print(f"{'='*60}\n")

    if results['corp_code_fail'] > total * 0.3:
        print("⚠️  고유번호 조회 실패가 많음")
        print("   → 종목 코드가 잘못되었거나 비상장 종목일 가능성")

    if results['financial_fail'] > total * 0.3:
        print("\n⚠️  재무제표 조회 실패가 많음")
        print("   → 2023년 사업보고서가 없는 종목")
        print("   → 신규 상장사 또는 폐업/합병 종목")
        print("   💡 해결책: 2022년 또는 2024년 데이터 시도")

    if results['cashflow_fail'] > total * 0.3:
        print("\n⚠️  현금흐름표 조회 실패가 많음")
        print("   → 현금흐름표 미작성 종목")
        print("   → 계정명 매칭 실패")
        print("   💡 해결책: 계정명 검색 패턴 확대")

    # 추가 테스트: 2022년, 2024년으로 재시도
    print(f"\n{'='*60}")
    print(f"🔬 추가 테스트: 다른 연도 시도")
    print(f"{'='*60}\n")

    # 실패한 종목 중 5개 샘플
    failed_stocks = [f for f in fail_examples if '재무제표 없음' in f['fail_stage']][:5]

    if len(failed_stocks) > 0:
        print(f"2023년 실패 종목을 2022년, 2024년으로 재시도...\n")

        for fail in failed_stocks:
            print(f"📊 {fail['name']} ({fail['code']})")
            corp_code = client.get_company_code(fail['code'])

            if corp_code:
                for year in ['2024', '2022', '2021']:
                    df_fs = client.get_financial_statements(corp_code, year, '11011')
                    if df_fs is not None and len(df_fs) > 0:
                        print(f"   ✅ {year}년 재무제표 있음!")
                        break
                    else:
                        print(f"   ❌ {year}년 재무제표 없음")

            time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"✅ 분석 완료")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    debug_opendart()
