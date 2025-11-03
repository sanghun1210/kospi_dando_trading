"""
F-Score 전략 간소화 백테스팅

현재 F-Score 6점 만점 종목들의 과거 수익률 검증
- 최근 1년간 실제 주가 수익률 계산
- KOSPI 벤치마크는 제외 (API 이슈)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pykrx import stock
import time


class SimpleFScoreBacktester:
    """간소화된 F-Score 백테스터"""

    def __init__(self):
        self.results = []

    def get_stock_return(self, code, name, start_date, end_date):
        """
        종목의 기간 수익률 계산

        Parameters:
        -----------
        code : str
            종목 코드
        name : str
            종목명
        start_date : str
            시작일 (YYYYMMDD)
        end_date : str
            종료일 (YYYYMMDD)

        Returns:
        --------
        result : dict
            {code, name, start_price, end_price, return, success}
        """
        try:
            # 시작일 기준 전후 10일 범위에서 데이터 가져오기
            start_range_begin = (datetime.strptime(start_date, '%Y%m%d') - timedelta(days=10)).strftime('%Y%m%d')
            start_range_end = (datetime.strptime(start_date, '%Y%m%d') + timedelta(days=10)).strftime('%Y%m%d')

            df_start = stock.get_market_ohlcv_by_date(start_range_begin, start_range_end, code)

            if len(df_start) == 0:
                return {'code': code, 'name': name, 'success': False, 'reason': 'No start data'}

            start_price = df_start.iloc[0]['종가']  # 가장 빠른 거래일

            # 종료일 기준 전후 10일 범위에서 데이터 가져오기
            end_range_begin = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=10)).strftime('%Y%m%d')

            df_end = stock.get_market_ohlcv_by_date(end_range_begin, end_date, code)

            if len(df_end) == 0:
                return {'code': code, 'name': name, 'success': False, 'reason': 'No end data'}

            end_price = df_end.iloc[-1]['종가']  # 가장 최근 거래일

            # 수익률 계산
            if start_price > 0:
                ret = (end_price - start_price) / start_price * 100
            else:
                return {'code': code, 'name': name, 'success': False, 'reason': 'Invalid start price'}

            return {
                'code': code,
                'name': name,
                'start_price': start_price,
                'end_price': end_price,
                'return': ret,
                'success': True
            }

        except Exception as e:
            return {'code': code, 'name': name, 'success': False, 'reason': str(e)}

    def backtest_portfolio(self, candidates_file, min_score=6, max_stocks=30,
                           start_date='20231101', end_date='20241101'):
        """
        포트폴리오 백테스팅

        Parameters:
        -----------
        candidates_file : str
            F-Score 후보 CSV
        min_score : int
            최소 점수
        max_stocks : int
            최대 보유 종목 수
        start_date : str
            시작일 (YYYYMMDD)
        end_date : str
            종료일 (YYYYMMDD)
        """
        print(f"\n{'='*60}")
        print(f"📊 F-Score 간소화 백테스팅")
        print(f"  - 기간: {start_date} ~ {end_date}")
        print(f"  - 최소 점수: {min_score}점")
        print(f"  - 최대 보유: {max_stocks}개")
        print(f"{'='*60}\n")

        # 1. F-Score 후보 로드
        df_candidates = pd.read_csv(candidates_file)
        df_candidates = df_candidates[df_candidates['score'] >= min_score].copy()

        print(f"📂 F-Score {min_score}점 이상: {len(df_candidates)}개 종목")

        if len(df_candidates) == 0:
            print("⚠️  조건을 만족하는 종목이 없습니다.")
            return None

        # 상위 N개 선택
        df_portfolio = df_candidates.head(max_stocks).copy()
        print(f"  → 상위 {len(df_portfolio)}개 종목 선택\n")

        # 2. 각 종목의 수익률 계산
        print(f"💹 종목별 수익률 계산 중...\n")

        results = []
        success_count = 0
        fail_count = 0

        for idx, row in df_portfolio.iterrows():
            code = row['code']
            name = row['name']

            result = self.get_stock_return(code, name, start_date, end_date)
            results.append(result)

            if result['success']:
                success_count += 1
                print(f"  ✅ {name} ({code}): {result['return']:+.2f}% "
                      f"({result['start_price']:,}원 → {result['end_price']:,}원)")
            else:
                fail_count += 1
                if idx < 5:  # 처음 5개만 에러 표시
                    print(f"  ❌ {name} ({code}): {result.get('reason', 'Unknown error')}")

            time.sleep(0.3)  # API 과부하 방지

        print(f"\n{'='*60}")
        print(f"✅ 수익률 계산 완료")
        print(f"  - 성공: {success_count}개")
        print(f"  - 실패: {fail_count}개")
        print(f"{'='*60}\n")

        # 3. 통계 계산
        successful_results = [r for r in results if r['success']]

        if len(successful_results) == 0:
            print("⚠️  성공한 종목이 없습니다.")
            return None

        returns = [r['return'] for r in successful_results]

        avg_return = np.mean(returns)
        median_return = np.median(returns)
        std_return = np.std(returns)
        min_return = np.min(returns)
        max_return = np.max(returns)

        win_count = sum(1 for r in returns if r > 0)
        win_rate = win_count / len(returns) * 100

        print(f"📈 포트폴리오 성과 분석 ({len(successful_results)}개 종목)")
        print(f"{'='*60}")
        print(f"  평균 수익률: {avg_return:+.2f}%")
        print(f"  중앙값: {median_return:+.2f}%")
        print(f"  표준편차: {std_return:.2f}%")
        print(f"  최대 수익: {max_return:+.2f}%")
        print(f"  최대 손실: {min_return:+.2f}%")
        print(f"  승률: {win_rate:.1f}% ({win_count}/{len(returns)})")
        print(f"{'='*60}\n")

        # 4. 상위/하위 종목
        df_results = pd.DataFrame(successful_results)
        df_results = df_results.sort_values('return', ascending=False)

        print(f"🏆 수익률 상위 10개 종목:")
        for i, (idx, row) in enumerate(df_results.head(10).iterrows(), 1):
            print(f"  {i}. {row['name']} ({row['code']}): {row['return']:+.2f}%")

        print(f"\n📉 수익률 하위 5개 종목:")
        for i, (idx, row) in enumerate(df_results.tail(5).iterrows(), 1):
            print(f"  {i}. {row['name']} ({row['code']}): {row['return']:+.2f}%")

        print()

        # 5. 결과 저장
        today = datetime.now().strftime('%Y%m%d')
        filename = f'backtest_simple_results_{today}.csv'
        df_results.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 결과 저장: {filename}\n")

        return {
            'avg_return': avg_return,
            'median_return': median_return,
            'std_return': std_return,
            'win_rate': win_rate,
            'results': df_results
        }


def main():
    """메인 실행"""
    print("=" * 60)
    print("🚀 F-Score 간소화 백테스팅 시스템")
    print("=" * 60)

    backtester = SimpleFScoreBacktester()

    # 최근 1년 백테스팅 (2023.11 ~ 2024.11)
    results = backtester.backtest_portfolio(
        candidates_file='fscore_parallel_results_20251101.csv',
        min_score=6,
        max_stocks=30,
        start_date='20231101',
        end_date='20241101'
    )

    if results:
        print("✅ 백테스팅 완료!")
        print(f"\n📊 결론:")
        if results['avg_return'] > 0:
            print(f"  F-Score 6점 만점 전략은 최근 1년간 평균 {results['avg_return']:+.2f}%의 수익을 기록했습니다.")
            print(f"  승률 {results['win_rate']:.1f}%로, {len(results['results'])}개 종목 중 "
                  f"{int(len(results['results']) * results['win_rate'] / 100)}개가 수익을 냈습니다.")
        else:
            print(f"  F-Score 6점 만점 전략은 최근 1년간 평균 {results['avg_return']:+.2f}%의 손실을 기록했습니다.")
            print(f"  ⚠️  추가 분석이 필요합니다.")


if __name__ == "__main__":
    main()
