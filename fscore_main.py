"""
F-Score 기반 주식 선정 메인 스크립트

워크플로우:
1. 종목 리스트 가져오기
2. 각 종목에 대해 Lite F-Score 계산
3. 점수 기준으로 정렬
4. 상위 종목 선정
5. 결과 저장 및 출력
"""

import pandas as pd
from datetime import datetime
from lite_fscore import LiteFScoreCalculator
from stock_screener import StockScreener
import time


class FScoreStockSelector:
    """F-Score 기반 주식 선정"""

    def __init__(self, use_existing_data=False):
        """
        Parameters:
        -----------
        use_existing_data : bool
            기존 df_sorted.csv 사용 여부 (True면 새로 수집 안 함)
        """
        self.use_existing_data = use_existing_data
        self.results = []

    def get_ticker_list(self):
        """종목 리스트 가져오기"""
        if self.use_existing_data:
            print("📂 기존 데이터 로드 중 (df_sorted.csv)...")
            try:
                df = pd.read_csv('df_sorted.csv', sep='\t', encoding='utf-8')
                print(f"✅ {len(df)}개 종목 데이터 로드 완료")
                return df[['Code', 'Name']].values.tolist()
            except Exception as e:
                print(f"⚠️  기존 데이터 로드 실패: {e}")
                print("→ 새로 종목 리스트 수집합니다...")
                self.use_existing_data = False

        # 새로 수집
        screener = StockScreener()
        df_filtered = screener.screen()
        return df_filtered[['Code', 'Name']].values.tolist()

    def calculate_fscores(self, ticker_list, max_count=None):
        """
        모든 종목에 대해 F-Score 계산

        Parameters:
        -----------
        ticker_list : list
            [(code, name), ...] 형태의 종목 리스트
        max_count : int
            최대 처리 종목 수 (테스트용, None이면 전체)

        Returns:
        --------
        results : list
            [{code, name, score, details}, ...]
        """
        print(f"\n{'='*60}")
        print(f"📊 F-Score 계산 시작")
        print(f"{'='*60}")

        if max_count:
            ticker_list = ticker_list[:max_count]
            print(f"⚠️  테스트 모드: 상위 {max_count}개 종목만 처리")

        total = len(ticker_list)
        results = []
        success_count = 0
        fail_count = 0

        start_time = time.time()

        for idx, (code, name) in enumerate(ticker_list, 1):
            try:
                # 진행률 표시
                if idx % 10 == 0 or idx == total:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / idx
                    remaining = avg_time * (total - idx)
                    print(f"  진행: {idx}/{total} ({idx/total*100:.1f}%) | "
                          f"성공: {success_count} | 실패: {fail_count} | "
                          f"예상 남은 시간: {remaining/60:.1f}분")

                # F-Score 계산
                calculator = LiteFScoreCalculator(code)
                score, details = calculator.calculate()

                if score is not None:
                    results.append({
                        'code': code,
                        'name': name,
                        'score': score,
                        'details': details
                    })
                    success_count += 1
                else:
                    fail_count += 1

                # API 과부하 방지 (0.5초 대기)
                time.sleep(0.5)

            except Exception as e:
                fail_count += 1
                if idx % 50 == 0:  # 50개마다 한 번씩만 에러 출력
                    print(f"    ⚠️  {code} ({name}) 처리 실패: {e}")

        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ F-Score 계산 완료")
        print(f"  - 총 처리: {total}개")
        print(f"  - 성공: {success_count}개")
        print(f"  - 실패: {fail_count}개")
        print(f"  - 소요 시간: {elapsed/60:.1f}분")
        print(f"{'='*60}\n")

        self.results = results
        return results

    def filter_and_rank(self, min_score=4):
        """
        결과 필터링 및 정렬

        Parameters:
        -----------
        min_score : int
            최소 점수 (기본값: 4점 이상)

        Returns:
        --------
        df_ranked : DataFrame
            정렬된 결과
        """
        print(f"🔍 필터링 및 정렬 (최소 점수: {min_score}점)")

        # DataFrame으로 변환
        df = pd.DataFrame(self.results)

        if len(df) == 0:
            print("⚠️  결과가 없습니다.")
            return pd.DataFrame()

        # 필터링
        df_filtered = df[df['score'] >= min_score].copy()
        print(f"  {min_score}점 이상: {len(df_filtered)}개 (전체: {len(df)}개)")

        # 정렬 (점수 내림차순)
        df_ranked = df_filtered.sort_values('score', ascending=False).reset_index(drop=True)

        return df_ranked

    def save_results(self, df, filename=None):
        """결과 저장"""
        if filename is None:
            today = datetime.now().strftime('%Y%m%d')
            filename = f'fscore_results_{today}.csv'

        # 상세 정보는 별도 컬럼으로 저장
        df_save = df.copy()

        # details를 개별 컬럼으로 분리
        if len(df_save) > 0 and 'details' in df_save.columns:
            detail_cols = []
            for key in df_save['details'].iloc[0].keys():
                df_save[key] = df_save['details'].apply(lambda x: x.get(key))
                detail_cols.append(key)

            # details 컬럼 제거
            df_save = df_save.drop('details', axis=1)

        df_save.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 결과 저장: {filename}")

        return filename

    def print_summary(self, df, top_n=20):
        """결과 요약 출력"""
        if len(df) == 0:
            print("결과가 없습니다.")
            return

        print(f"\n{'='*60}")
        print(f"📈 상위 {top_n}개 종목 (F-Score 기준)")
        print(f"{'='*60}\n")

        for idx, row in df.head(top_n).iterrows():
            print(f"{idx+1}. {row['name']} ({row['code']})")
            print(f"   F-Score: {row['score']}/6 ⭐")

            # 상세 정보
            details = row['details']
            print(f"   ✅ 당기순이익 > 0: {details.get('net_income_positive', 'N/A')}")
            print(f"   ✅ ROA 증가: {details.get('roa_increasing', 'N/A')}", end='')
            if details.get('roa_current'):
                print(f" ({details['roa_previous']}% → {details['roa_current']}%)")
            else:
                print()
            print(f"   ✅ 부채비율 감소: {details.get('debt_ratio_decreasing', 'N/A')}", end='')
            if details.get('debt_ratio_current'):
                print(f" ({details['debt_ratio_previous']}% → {details['debt_ratio_current']}%)")
            else:
                print()
            print(f"   ✅ 발행주식수 불변/감소: {details.get('shares_not_increasing', 'N/A')}")
            print(f"   ✅ 영업이익률 증가: {details.get('operating_margin_increasing', 'N/A')}", end='')
            if details.get('operating_margin_current'):
                print(f" ({details['operating_margin_previous']}% → {details['operating_margin_current']}%)")
            else:
                print()
            print(f"   ✅ 자산회전율 증가: {details.get('asset_turnover_increasing', 'N/A')}")
            print()

        print(f"{'='*60}\n")

    def generate_email_report(self, df, top_n=20):
        """이메일 리포트 생성 (HTML)"""
        if len(df) == 0:
            return "<p>이번 주에는 조건을 만족하는 종목이 없습니다.</p>"

        today = datetime.now().strftime('%Y년 %m월 %d일')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                .stock {{
                    border: 1px solid #ddd;
                    padding: 15px;
                    margin: 10px 0;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }}
                .score-high {{ background-color: #d4edda; }}
                .score-med {{ background-color: #fff3cd; }}
                .metric {{ margin: 5px 0; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>📊 F-Score 기반 주식 분석 리포트</h1>
            <p><strong>날짜:</strong> {today}</p>
            <p><strong>분석 종목 수:</strong> {len(df)}개</p>

            <h2>🎯 상위 {top_n}개 추천 종목</h2>
        """

        for idx, row in df.head(top_n).iterrows():
            score = row['score']
            score_class = 'score-high' if score >= 5 else 'score-med'
            details = row['details']

            html += f"""
            <div class="stock {score_class}">
                <h3>{idx+1}. {row['name']} ({row['code']})</h3>
                <p><strong>F-Score: {score}/6</strong></p>
                <div class="metric {'pass' if details.get('net_income_positive') else 'fail'}">
                    {'✅' if details.get('net_income_positive') else '❌'} 당기순이익 > 0
                </div>
                <div class="metric {'pass' if details.get('roa_increasing') else 'fail'}">
                    {'✅' if details.get('roa_increasing') else '❌'} ROA 증가
                    {f"({details.get('roa_previous')}% → {details.get('roa_current')}%)" if details.get('roa_current') else ''}
                </div>
                <div class="metric {'pass' if details.get('debt_ratio_decreasing') else 'fail'}">
                    {'✅' if details.get('debt_ratio_decreasing') else '❌'} 부채비율 감소
                    {f"({details.get('debt_ratio_previous')}% → {details.get('debt_ratio_current')}%)" if details.get('debt_ratio_current') else ''}
                </div>
                <div class="metric {'pass' if details.get('shares_not_increasing') else 'fail'}">
                    {'✅' if details.get('shares_not_increasing') else '❌'} 발행주식수 불변/감소
                </div>
                <div class="metric {'pass' if details.get('operating_margin_increasing') else 'fail'}">
                    {'✅' if details.get('operating_margin_increasing') else '❌'} 영업이익률 증가
                    {f"({details.get('operating_margin_previous')}% → {details.get('operating_margin_current')}%)" if details.get('operating_margin_current') else ''}
                </div>
                <div class="metric {'pass' if details.get('asset_turnover_increasing') else 'fail'}">
                    {'✅' if details.get('asset_turnover_increasing') else '❌'} 자산회전율 증가
                </div>
            </div>
            """

        html += """
            <hr>
            <p><em>본 리포트는 자동으로 생성되었습니다. 투자 판단의 참고자료로만 활용하시기 바랍니다.</em></p>
        </body>
        </html>
        """

        # HTML 파일로 저장
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f'fscore_report_{today_str}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"📧 이메일 리포트 생성: {filename}")
        return html


def main():
    """메인 실행"""
    print("="*60)
    print("🚀 F-Score 주식 선정 시스템")
    print("="*60)

    # 1. 초기화
    selector = FScoreStockSelector(use_existing_data=True)

    # 2. 종목 리스트 가져오기
    ticker_list = selector.get_ticker_list()

    # 3. F-Score 계산 (상위 200개로 테스트)
    # 전체 실행: max_count=None
    results = selector.calculate_fscores(ticker_list, max_count=200)

    # 4. 필터링 및 정렬 (4점 이상)
    df_ranked = selector.filter_and_rank(min_score=4)

    # 5. 결과 저장
    if len(df_ranked) > 0:
        selector.save_results(df_ranked)

        # 6. 요약 출력
        selector.print_summary(df_ranked, top_n=20)

        # 7. 이메일 리포트 생성
        selector.generate_email_report(df_ranked, top_n=20)

        print("\n✅ 모든 작업 완료!")
    else:
        print("\n⚠️  조건을 만족하는 종목이 없습니다.")


if __name__ == "__main__":
    main()
