"""
병렬 처리 F-Score 계산 (멀티스레딩)

기존 fscore_main.py 대비 10배 빠름
- 순차 처리: 2,600개 → 29분
- 병렬 처리: 2,600개 → 3-5분
"""

import pandas as pd
from datetime import datetime
from lite_fscore import LiteFScoreCalculator
from stock_screener import StockScreener
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


class ParallelFScoreSelector:
    """병렬 처리 F-Score 계산기"""

    def __init__(self, use_existing_data=False, max_workers=8, opendart_client=None):
        """
        Parameters:
        -----------
        use_existing_data : bool
            기존 df_sorted.csv 사용 여부
        max_workers : int
            동시 처리 스레드 수 (기본값: 8)
            - 너무 많으면 FnGuide가 차단할 수 있음
            - 네트워크 품질에 따라 조정 가능
        """
        self.use_existing_data = use_existing_data
        self.max_workers = max_workers
        self.results = []
        self.lock = Lock()  # 스레드 안전성을 위한 락
        self.opendart_client = opendart_client

        # 통계
        self.success_count = 0
        self.fail_count = 0

    def get_ticker_list(self):
        """종목 리스트 가져오기"""
        if self.use_existing_data:
            print("📂 기존 데이터 로드 중 (df_sorted.csv)...")
            try:
                df = pd.read_csv('df_sorted.csv', sep='\t', encoding='utf-8')
                df['Code'] = df['Code'].astype(str).str.zfill(6)
                print(f"✅ {len(df)}개 종목 데이터 로드 완료")
                return df[['Code', 'Name']].values.tolist()
            except Exception as e:
                print(f"⚠️  기존 데이터 로드 실패: {e}")
                print("→ 새로 종목 리스트 수집합니다...")
                self.use_existing_data = False

        # 새로 수집
        screener = StockScreener()
        df_filtered = screener.screen()
        df_filtered['Code'] = df_filtered['Code'].astype(str).str.zfill(6)
        return df_filtered[['Code', 'Name']].values.tolist()

    def process_single_ticker(self, code, name, idx, total):
        """
        단일 종목 처리 (스레드에서 실행)

        Returns:
        --------
        result : dict or None
        """
        try:
            # F-Score 계산
            calculator = LiteFScoreCalculator(code, opendart_client=self.opendart_client)
            score, details = calculator.calculate()

            if score is not None:
                result = {
                    'code': code,
                    'name': name,
                    'score': score,
                    'details': details
                }

                # 스레드 안전하게 통계 업데이트
                with self.lock:
                    self.success_count += 1
                    self.results.append(result)

                return result
            else:
                reason = getattr(calculator, 'last_error', '데이터 부족')
                with self.lock:
                    self.fail_count += 1
                print(f"[FAIL] {code} {name}: {reason}")
                return None

        except Exception as e:
            with self.lock:
                self.fail_count += 1
            print(f"[ERROR] {code} {name}: {e}")
            return None

    def calculate_fscores_parallel(self, ticker_list, max_count=None):
        """
        병렬로 모든 종목에 대해 F-Score 계산

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
        print(f"🚀 병렬 F-Score 계산 시작 (동시 처리: {self.max_workers}개)")
        print(f"{'='*60}")

        if max_count:
            ticker_list = ticker_list[:max_count]
            print(f"⚠️  테스트 모드: 상위 {max_count}개 종목만 처리")

        total = len(ticker_list)
        start_time = time.time()

        # 진행률 표시를 위한 카운터
        processed = 0
        last_print_time = time.time()

        # ThreadPoolExecutor로 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 작업 제출
            future_to_ticker = {
                executor.submit(self.process_single_ticker, code, name, idx, total): (code, name)
                for idx, (code, name) in enumerate(ticker_list, 1)
            }

            # 완료되는 대로 결과 수집
            for future in as_completed(future_to_ticker):
                processed += 1

                # 10개마다 또는 1초마다 진행률 출력
                current_time = time.time()
                if processed % 10 == 0 or (current_time - last_print_time) > 1.0 or processed == total:
                    elapsed = current_time - start_time
                    avg_time = elapsed / processed if processed > 0 else 0
                    remaining = avg_time * (total - processed)

                    print(f"  진행: {processed}/{total} ({processed/total*100:.1f}%) | "
                          f"성공: {self.success_count} | 실패: {self.fail_count} | "
                          f"경과: {elapsed/60:.1f}분 | 예상 남은 시간: {remaining/60:.1f}분")

                    last_print_time = current_time

        elapsed = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"✅ 병렬 F-Score 계산 완료")
        print(f"  - 총 처리: {total}개")
        print(f"  - 성공: {self.success_count}개 ({self.success_count/total*100:.1f}%)")
        print(f"  - 실패: {self.fail_count}개")
        print(f"  - 소요 시간: {elapsed/60:.1f}분")
        print(f"  - 평균 처리 속도: {total/elapsed:.1f}개/초")
        print(f"  - 순차 처리 대비: {0.66*total/60/elapsed:.1f}배 빠름")
        print(f"{'='*60}\n")

        return self.results

    def filter_and_rank(self, min_score=4):
        """결과 필터링 및 정렬"""
        print(f"🔍 필터링 및 정렬 (최소 점수: {min_score}점)")

        df = pd.DataFrame(self.results)

        if len(df) == 0:
            print("⚠️  결과가 없습니다.")
            return pd.DataFrame()

        # 필터링
        df_filtered = df[df['score'] >= min_score].copy()
        print(f"  {min_score}점 이상: {len(df_filtered)}개 (전체: {len(df)}개)")

        # 정렬
        df_ranked = df_filtered.sort_values('score', ascending=False).reset_index(drop=True)

        return df_ranked

    def save_results(self, df, filename=None):
        """결과 저장"""
        if filename is None:
            today = datetime.now().strftime('%Y%m%d')
            filename = f'fscore_parallel_results_{today}.csv'

        # details를 개별 컬럼으로 분리
        df_save = df.copy()

        if len(df_save) > 0 and 'details' in df_save.columns:
            for key in df_save['details'].iloc[0].keys():
                df_save[key] = df_save['details'].apply(lambda x: x.get(key))

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
            score_stars = "⭐" * row['score']
            print(f"{idx+1}. {row['name']} ({row['code']}) - {row['score']}/6 {score_stars}")

        print(f"\n{'='*60}")
        print(f"📊 점수 분포:")
        score_counts = df['score'].value_counts().sort_index(ascending=False)
        for score, count in score_counts.items():
            print(f"  {score}점: {count}개")
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
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                .summary {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .stock {{
                    border: 1px solid #ddd;
                    padding: 15px;
                    margin: 10px 0;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }}
                .score-6 {{ background-color: #d4edda; border-left: 5px solid #28a745; }}
                .score-5 {{ background-color: #fff3cd; border-left: 5px solid #ffc107; }}
                .score-4 {{ background-color: #f8d7da; border-left: 5px solid #dc3545; }}
                .metric {{ margin: 5px 0; }}
                .pass {{ color: green; font-weight: bold; }}
                .fail {{ color: #999; }}
            </style>
        </head>
        <body>
            <h1>📊 F-Score 기반 주식 분석 리포트</h1>

            <div class="summary">
                <p><strong>날짜:</strong> {today}</p>
                <p><strong>분석 종목 수:</strong> {len(df)}개</p>
                <p><strong>처리 시간:</strong> 병렬 처리 (고속)</p>
            </div>

            <h2>🎯 상위 {top_n}개 추천 종목</h2>
        """

        for idx, row in df.head(top_n).iterrows():
            score = row['score']
            score_class = f'score-{score}'
            details = row['details']

            html += f"""
            <div class="stock {score_class}">
                <h3>{idx+1}. {row['name']} ({row['code']}) - {score}/6점</h3>
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
            <p><em>본 리포트는 F-Score 전략을 기반으로 자동 생성되었습니다. 투자 판단의 참고자료로만 활용하시기 바랍니다.</em></p>
        </body>
        </html>
        """

        # HTML 파일로 저장
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f'fscore_parallel_report_{today_str}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"📧 이메일 리포트 생성: {filename}")
        return html


def main():
    """메인 실행"""
    print("="*60)
    print("🚀 병렬 처리 F-Score 주식 선정 시스템")
    print("="*60)

    # 1. 초기화 (동시 15개 처리)
    selector = ParallelFScoreSelector(use_existing_data=True, max_workers=8)

    # 2. 종목 리스트 가져오기
    ticker_list = selector.get_ticker_list()

    # 3. 병렬 F-Score 계산 (전체)
    results = selector.calculate_fscores_parallel(ticker_list, max_count=None)

    # 4. 필터링 및 정렬
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
