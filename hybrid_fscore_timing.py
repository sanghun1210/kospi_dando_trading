"""
F-Score + 기술적 분석 통합 모듈

재무 우량 종목(F-Score) + 최적 매수 타이밍(차트)
"""

import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os

from technical_data_collector import TechnicalDataCollector
from technical_indicators import TechnicalIndicators
from timing_signals import TimingSignals


class HybridFScoreTiming:
    """F-Score + 타이밍 분석 통합 시스템"""

    def __init__(self, fscore_csv_path=None, min_fscore=4, checkpoint_interval=20):
        """
        Parameters:
        -----------
        fscore_csv_path : str
            F-Score 결과 CSV 파일 경로
        min_fscore : int
            최소 F-Score (기본: 4점)
        checkpoint_interval : int
            체크포인트 저장 간격 (기본: 20개마다)
        """
        self.fscore_csv_path = fscore_csv_path
        self.min_fscore = min_fscore
        self.fscore_stocks = None
        self.results = []
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_path = None

    def load_fscore_results(self):
        """
        F-Score 결과 로드

        Returns:
        --------
        df : DataFrame
            F-Score 우량 종목 리스트
        """
        if self.fscore_csv_path is None:
            print("⚠️  F-Score 결과 파일 경로가 지정되지 않았습니다.")
            return None

        try:
            df = pd.read_csv(self.fscore_csv_path)

            # 컬럼명 표준화 (대소문자 처리)
            df.columns = df.columns.str.title().str.replace('_', ' ').str.replace(' ', '_')

            # F-Score로 필터링
            score_col = 'Score' if 'Score' in df.columns else 'F_Score'
            df_filtered = df[df[score_col] >= self.min_fscore].copy()

            print(f"✅ F-Score 결과 로드 완료")
            print(f"  전체: {len(df)}개")
            print(f"  {self.min_fscore}점 이상: {len(df_filtered)}개")

            self.fscore_stocks = df_filtered
            return df_filtered

        except Exception as e:
            print(f"❌ F-Score 결과 로드 실패: {e}")
            return None

    def analyze_single_stock(self, row):
        """
        단일 종목 분석 (F-Score + 타이밍)

        Parameters:
        -----------
        row : Series
            F-Score 결과 행

        Returns:
        --------
        result : dict
            통합 분석 결과
        """
        ticker = row['Code']
        name = row['Name']
        fscore = row.get('Score', row.get('F_Score', row.get('F-Score', 0)))

        try:
            # 1. 차트 데이터 수집
            collector = TechnicalDataCollector(days=120)
            df = collector.get_ohlcv(ticker)

            if df is None or len(df) < 60:
                return None

            # 2. 기술적 지표 계산
            indicators = TechnicalIndicators(df)
            df_with_indicators = indicators.calculate_all()

            # 3. 타이밍 신호 검출
            signals = TimingSignals(df_with_indicators)
            timing_result = signals.calculate_timing_score()

            # 4. 통합 점수 계산
            # F-Score * 10 + 타이밍 * 5 (최대 90 + 50 = 140점)
            combined_score = fscore * 10 + timing_result['score'] * 5

            # 5. 최신 가격 정보
            latest_close = df['Close'].iloc[-1]
            change_30d = collector.get_price_change(ticker, 30)

            result = {
                'Code': ticker,
                'Name': name,
                'F-Score': fscore,
                'Timing_Score': timing_result['score'],
                'Combined_Score': round(combined_score, 2),
                'Rating': timing_result['rating'],
                'Recommendation': timing_result['recommendation'],
                'Current_Price': int(latest_close),
                'Change_30D': change_30d,
                'Signals': ', '.join(timing_result['details'][:3]),  # 상위 3개만
            }

            # ROA 등 추가 정보
            if 'Roa_Current' in row:
                result['ROA'] = row['Roa_Current']
            elif 'ROA_current' in row:
                result['ROA'] = row['ROA_current']

            return result

        except Exception as e:
            print(f"  ⚠️  {name} ({ticker}) 분석 실패: {e}")
            return None

    def save_checkpoint(self, results, checkpoint_num):
        """중간 체크포인트 저장"""
        if self.checkpoint_path is None:
            today = datetime.now().strftime('%Y%m%d')
            self.checkpoint_path = f'hybrid_timing_checkpoint_{today}.csv'

        if len(results) > 0:
            df = pd.DataFrame(results)
            df = df.sort_values('Combined_Score', ascending=False)
            df.to_csv(self.checkpoint_path, index=False, encoding='utf-8-sig')
            print(f"  💾 체크포인트 저장: {len(results)}개 ({self.checkpoint_path})")

    def load_checkpoint(self):
        """체크포인트에서 복구"""
        if self.checkpoint_path and os.path.exists(self.checkpoint_path):
            try:
                df = pd.read_csv(self.checkpoint_path)
                print(f"  ♻️  체크포인트에서 {len(df)}개 복구됨")
                return df.to_dict('records')
            except Exception as e:
                print(f"  ⚠️  체크포인트 로드 실패: {e}")
        return []

    def analyze_batch(self, ticker_list=None, max_workers=3, max_count=None, resume=True):
        """
        배치 분석 (병렬 처리, 체크포인트 지원)

        Parameters:
        -----------
        ticker_list : list
            분석할 종목 리스트 (None이면 전체)
        max_workers : int
            병렬 처리 워커 수 (기본: 3, 안정성↑)
        max_count : int
            최대 분석 종목 수
        resume : bool
            체크포인트에서 재개 여부 (기본: True)

        Returns:
        --------
        results_df : DataFrame
            통합 분석 결과
        """
        if self.fscore_stocks is None:
            print("❌ F-Score 결과를 먼저 로드하세요")
            return None

        # 분석 대상 결정
        if ticker_list is None:
            stocks_to_analyze = self.fscore_stocks
        else:
            stocks_to_analyze = self.fscore_stocks[
                self.fscore_stocks['Code'].isin(ticker_list)
            ]

        # 최대 개수 제한
        if max_count:
            stocks_to_analyze = stocks_to_analyze.head(max_count)

        # 체크포인트 설정
        today = datetime.now().strftime('%Y%m%d')
        self.checkpoint_path = f'hybrid_timing_checkpoint_{today}.csv'

        # 체크포인트에서 복구
        results = []
        processed_tickers = set()
        if resume and os.path.exists(self.checkpoint_path):
            results = self.load_checkpoint()
            processed_tickers = {r['Code'] for r in results}
            stocks_to_analyze = stocks_to_analyze[
                ~stocks_to_analyze['Code'].isin(processed_tickers)
            ]

        total_original = len(stocks_to_analyze) + len(processed_tickers)
        total = len(stocks_to_analyze)

        print(f"\n🚀 통합 분석 시작")
        print(f"  전체: {total_original}개")
        if len(processed_tickers) > 0:
            print(f"  이미 완료: {len(processed_tickers)}개 (체크포인트)")
            print(f"  남은 종목: {total}개")
        print(f"  F-Score >= {self.min_fscore}")
        print(f"  병렬 처리: {max_workers} workers")
        print(f"  체크포인트: {self.checkpoint_interval}개마다 저장")

        if total == 0:
            print(f"✅ 모든 종목 분석 완료 (체크포인트에서 복구)\n")
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Combined_Score', ascending=False)
            results_df = results_df.reset_index(drop=True)
            results_df.index = results_df.index + 1
            self.results = results_df
            return results_df

        lock = Lock()
        checkpoint_counter = len(processed_tickers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.analyze_single_stock, row): idx
                for idx, row in stocks_to_analyze.iterrows()
            }

            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30초 타임아웃

                    with lock:
                        if result is not None:
                            results.append(result)

                        completed += 1
                        checkpoint_counter += 1

                        # 진행 상황 출력
                        if completed % 10 == 0 or completed == total:
                            print(f"  진행: {len(processed_tickers) + completed}/{total_original} "
                                  f"(성공: {len(results)}개)")

                        # 체크포인트 저장
                        if checkpoint_counter % self.checkpoint_interval == 0:
                            self.save_checkpoint(results, checkpoint_counter)

                except Exception as e:
                    print(f"  ⚠️  분석 중 오류: {e}")
                    completed += 1

        # 최종 저장
        if len(results) > len(processed_tickers):
            self.save_checkpoint(results, len(results))

        print(f"✅ 분석 완료: {len(results)}/{total_original}개\n")

        # DataFrame 변환 및 정렬
        if len(results) > 0:
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Combined_Score', ascending=False)
            results_df = results_df.reset_index(drop=True)
            results_df.index = results_df.index + 1  # 1부터 시작

            self.results = results_df
            return results_df
        else:
            return None

    def save_results(self, output_path=None):
        """
        결과 저장

        Parameters:
        -----------
        output_path : str
            출력 파일 경로 (None이면 자동 생성)
        """
        if self.results is None or len(self.results) == 0:
            print("❌ 저장할 결과가 없습니다")
            return

        if output_path is None:
            today = datetime.now().strftime('%Y%m%d')
            output_path = f'hybrid_timing_results_{today}.csv'

        self.results.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 결과 저장: {output_path}")

    def print_top_picks(self, top_n=20):
        """
        상위 종목 출력

        Parameters:
        -----------
        top_n : int
            출력할 종목 수
        """
        if self.results is None or len(self.results) == 0:
            print("❌ 결과가 없습니다")
            return

        print("\n" + "=" * 80)
        print(f"🏆 TOP {top_n} 매수 추천 종목 (F-Score + 타이밍 통합)")
        print("=" * 80)

        top_stocks = self.results.head(top_n)

        for idx, row in top_stocks.iterrows():
            print(f"\n{idx}. {row['Name']} ({row['Code']})")
            print(f"  종합 점수: {row['Combined_Score']:.1f}점")
            print(f"  - F-Score: {row['F-Score']}/6 | 타이밍: {row['Timing_Score']:.1f}/10")
            print(f"  - 등급: {row['Rating']} | 추천: {row['Recommendation']}")
            print(f"  - 현재가: {row['Current_Price']:,}원 | 30일 변화: {row['Change_30D']:.1f}%")
            print(f"  - 시그널: {row['Signals']}")

        print("\n" + "=" * 80)


def main():
    """메인 실행"""
    print("🎯 F-Score + 타이밍 분석 통합 시스템\n")

    # CSV 파일 찾기 (최신 파일)
    import glob
    csv_files = glob.glob('hybrid_lite_results_*.csv')

    if len(csv_files) == 0:
        csv_files = glob.glob('fscore_parallel_results_*.csv')

    if len(csv_files) == 0:
        print("❌ F-Score 결과 파일을 찾을 수 없습니다")
        print("  먼저 parallel_fscore.py 또는 hybrid_fscore.py를 실행하세요")
        return

    # 최신 파일 선택
    latest_csv = sorted(csv_files)[-1]
    print(f"📂 F-Score 결과: {latest_csv}\n")

    # 통합 분석 실행
    analyzer = HybridFScoreTiming(
        fscore_csv_path=latest_csv,
        min_fscore=4  # 4점 이상만 분석
    )

    # F-Score 결과 로드
    analyzer.load_fscore_results()

    # 배치 분석 (상위 50개만 테스트)
    print("\n⚠️  테스트 모드: 상위 50개 종목만 분석합니다")
    print("  전체 분석을 원하시면 max_count=None으로 변경하세요\n")

    results_df = analyzer.analyze_batch(
        max_workers=5,
        max_count=50  # 테스트: 50개만
    )

    if results_df is not None:
        # 상위 20개 출력
        analyzer.print_top_picks(top_n=20)

        # 결과 저장
        analyzer.save_results()

        # 통계
        print("\n📊 분석 통계")
        print(f"  평균 F-Score: {results_df['F-Score'].mean():.2f}")
        print(f"  평균 타이밍 점수: {results_df['Timing_Score'].mean():.2f}")
        print(f"  A등급 (타이밍 7점 이상): {len(results_df[results_df['Timing_Score'] >= 7])}개")
        print(f"  B등급 (타이밍 5~7점): {len(results_df[(results_df['Timing_Score'] >= 5) & (results_df['Timing_Score'] < 7)])}개")


if __name__ == "__main__":
    main()
