"""
F-Score 전략 백테스팅 시스템

과거 데이터로 F-Score 전략의 실제 수익률 검증
- 기간: 2021년 ~ 2024년 (3년)
- 리밸런싱: 분기별 (3개월)
- 벤치마크: KOSPI 지수
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pykrx import stock
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


class FScoreBacktester:
    """F-Score 전략 백테스터"""

    def __init__(self, start_date='20210101', end_date='20241031'):
        """
        Parameters:
        -----------
        start_date : str
            백테스팅 시작일 (YYYYMMDD)
        end_date : str
            백테스팅 종료일 (YYYYMMDD)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.rebalancing_dates = []
        self.portfolio_history = []
        self.kospi_history = []
        self.lock = Lock()

    def get_rebalancing_dates(self, frequency='quarterly'):
        """
        리밸런싱 날짜 생성

        Parameters:
        -----------
        frequency : str
            'quarterly' (분기별), 'monthly' (월별)
        """
        print(f"\n📅 리밸런싱 날짜 생성 ({frequency})...")

        start = datetime.strptime(self.start_date, '%Y%m%d')
        end = datetime.strptime(self.end_date, '%Y%m%d')

        dates = []
        current = start

        if frequency == 'quarterly':
            # 분기별 (3개월마다)
            while current <= end:
                dates.append(current.strftime('%Y%m%d'))
                # 3개월 후
                month = current.month + 3
                year = current.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                current = datetime(year, month, 1)

        elif frequency == 'monthly':
            # 월별
            while current <= end:
                dates.append(current.strftime('%Y%m%d'))
                # 1개월 후
                month = current.month + 1
                year = current.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                current = datetime(year, month, 1)

        self.rebalancing_dates = dates
        print(f"  ✅ {len(dates)}개 리밸런싱 날짜 생성")
        return dates

    def get_trading_date(self, target_date):
        """
        실제 거래일 찾기 (주말/공휴일 대응)

        Parameters:
        -----------
        target_date : str
            목표 날짜 (YYYYMMDD)

        Returns:
        --------
        trading_date : str
            실제 거래일
        """
        try:
            dt = datetime.strptime(target_date, '%Y%m%d')

            # 최대 7일 앞으로 탐색
            for i in range(7):
                check_date = (dt + timedelta(days=i)).strftime('%Y%m%d')
                # KOSPI 지수로 거래일 확인
                df = stock.get_index_ohlcv(check_date, check_date, "1001")  # KOSPI
                if len(df) > 0:
                    return check_date

            # 못 찾으면 원래 날짜 반환
            return target_date

        except Exception as e:
            return target_date

    def get_stock_price(self, code, date):
        """
        특정 날짜의 주가 가져오기

        Parameters:
        -----------
        code : str
            종목 코드
        date : str
            날짜 (YYYYMMDD)

        Returns:
        --------
        price : float
            종가 (실패 시 None)
        """
        try:
            # 해당 날짜 기준 최근 5영업일 데이터 가져오기
            end_date = date
            start_date = (datetime.strptime(date, '%Y%m%d') - timedelta(days=10)).strftime('%Y%m%d')

            df = stock.get_market_ohlcv_by_date(start_date, end_date, code)

            if len(df) > 0:
                return df.iloc[-1]['종가']  # 가장 최근 종가
            else:
                return None

        except Exception as e:
            return None

    def get_kospi_price(self, date):
        """
        KOSPI 지수 가져오기

        Parameters:
        -----------
        date : str
            날짜 (YYYYMMDD)

        Returns:
        --------
        index : float
            KOSPI 지수 (실패 시 None)
        """
        try:
            # 해당 날짜 기준 최대 20영업일 범위에서 탐색
            start_date = (datetime.strptime(date, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d')
            df = stock.get_index_ohlcv(start_date, date, "1001")  # KOSPI

            if len(df) > 0:
                return df.iloc[-1]['종가']
            else:
                return None

        except Exception as e:
            return None

    def simulate_portfolio(self, candidates_file, min_score=6, max_stocks=30):
        """
        포트폴리오 시뮬레이션

        Parameters:
        -----------
        candidates_file : str
            F-Score 후보 종목 CSV 파일 경로
        min_score : int
            최소 F-Score (기본값: 6점)
        max_stocks : int
            최대 보유 종목 수 (기본값: 30개)

        Returns:
        --------
        results : dict
            백테스팅 결과
        """
        print(f"\n{'='*60}")
        print(f"📊 F-Score 백테스팅 시작")
        print(f"  - 기간: {self.start_date} ~ {self.end_date}")
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

        # 2. 리밸런싱 날짜 생성
        self.get_rebalancing_dates(frequency='quarterly')

        # 3. 각 리밸런싱 기간마다 수익률 계산
        portfolio_values = []
        kospi_values = []

        initial_capital = 10000000  # 1천만원
        portfolio_value = initial_capital
        kospi_value = initial_capital

        # 첫 날짜의 KOSPI 지수 - 첫 리밸런싱 기간의 시작점으로 사용
        first_date = None
        kospi_start = None

        # 최대 30일 앞으로 탐색하여 거래일 찾기
        start_dt = datetime.strptime(self.rebalancing_dates[0], '%Y%m%d')
        for i in range(30):
            check_date = (start_dt + timedelta(days=i)).strftime('%Y%m%d')
            kospi_start = self.get_kospi_price(check_date)
            if kospi_start is not None:
                first_date = check_date
                break

        if kospi_start is None or first_date is None:
            print("⚠️  KOSPI 시작 지수를 가져올 수 없습니다.")
            return None

        print(f"🏁 시작: {first_date}")
        print(f"  - 초기 자본: {initial_capital:,}원")
        print(f"  - KOSPI 시작: {kospi_start:.2f}\n")

        # 리밸런싱 기간마다 처리
        for i in range(len(self.rebalancing_dates) - 1):
            start_date = self.get_trading_date(self.rebalancing_dates[i])
            end_date = self.get_trading_date(self.rebalancing_dates[i + 1])

            print(f"📈 기간 {i+1}: {start_date} ~ {end_date}")

            # 포트폴리오 각 종목의 수익률 계산
            returns = []

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {}

                for _, row in df_portfolio.iterrows():
                    code = row['code']
                    name = row['name']

                    future = executor.submit(self._calculate_stock_return, code, name, start_date, end_date)
                    futures[future] = (code, name)

                for future in as_completed(futures):
                    ret = future.result()
                    if ret is not None:
                        returns.append(ret)

            # 포트폴리오 평균 수익률 (동일 가중)
            if len(returns) > 0:
                avg_return = np.mean(returns)
                portfolio_value *= (1 + avg_return / 100)
                print(f"  포트폴리오 수익률: {avg_return:.2f}% (성공: {len(returns)}/{len(df_portfolio)}개)")
            else:
                print(f"  ⚠️  수익률 계산 실패")
                avg_return = 0

            # KOSPI 수익률
            kospi_end = self.get_kospi_price(end_date)
            if kospi_end and kospi_start:
                kospi_return = (kospi_end - kospi_start) / kospi_start * 100
                kospi_value *= (1 + kospi_return / 100)
                print(f"  KOSPI 수익률: {kospi_return:.2f}%")
                kospi_start = kospi_end
            else:
                kospi_return = 0

            portfolio_values.append({
                'date': end_date,
                'value': portfolio_value,
                'return': avg_return
            })

            kospi_values.append({
                'date': end_date,
                'value': kospi_value,
                'return': kospi_return
            })

            print(f"  누적 자산: {portfolio_value:,.0f}원 (KOSPI: {kospi_value:,.0f}원)\n")

            time.sleep(0.5)  # API 과부하 방지

        # 4. 최종 결과
        total_return = (portfolio_value - initial_capital) / initial_capital * 100
        kospi_total_return = (kospi_value - initial_capital) / initial_capital * 100
        excess_return = total_return - kospi_total_return

        print(f"\n{'='*60}")
        print(f"✅ 백테스팅 완료")
        print(f"{'='*60}")
        print(f"📊 최종 결과:")
        print(f"  - F-Score 전략: {portfolio_value:,.0f}원 ({total_return:+.2f}%)")
        print(f"  - KOSPI 벤치마크: {kospi_value:,.0f}원 ({kospi_total_return:+.2f}%)")
        print(f"  - 초과 수익: {excess_return:+.2f}%p")
        print(f"{'='*60}\n")

        results = {
            'initial_capital': initial_capital,
            'final_value': portfolio_value,
            'total_return': total_return,
            'kospi_final_value': kospi_value,
            'kospi_total_return': kospi_total_return,
            'excess_return': excess_return,
            'portfolio_history': portfolio_values,
            'kospi_history': kospi_values,
            'num_periods': len(self.rebalancing_dates) - 1
        }

        return results

    def _calculate_stock_return(self, code, name, start_date, end_date):
        """
        단일 종목의 수익률 계산 (스레드에서 실행)

        Returns:
        --------
        return : float
            수익률(%) 또는 None
        """
        try:
            start_price = self.get_stock_price(code, start_date)
            end_price = self.get_stock_price(code, end_date)

            if start_price and end_price and start_price > 0:
                ret = (end_price - start_price) / start_price * 100
                return ret
            else:
                return None

        except Exception as e:
            return None

    def calculate_metrics(self, results):
        """
        성과 지표 계산

        Parameters:
        -----------
        results : dict
            백테스팅 결과

        Returns:
        --------
        metrics : dict
            성과 지표
        """
        print(f"\n{'='*60}")
        print(f"📈 성과 지표 계산")
        print(f"{'='*60}\n")

        portfolio_history = results['portfolio_history']
        kospi_history = results['kospi_history']

        # 1. 연평균 수익률 (CAGR)
        years = len(portfolio_history) / 4  # 분기별이므로 4로 나눔
        cagr = (results['final_value'] / results['initial_capital']) ** (1 / years) - 1
        cagr *= 100

        kospi_cagr = (results['kospi_final_value'] / results['initial_capital']) ** (1 / years) - 1
        kospi_cagr *= 100

        print(f"📊 연평균 수익률 (CAGR):")
        print(f"  - F-Score: {cagr:.2f}%")
        print(f"  - KOSPI: {kospi_cagr:.2f}%")

        # 2. 최대 낙폭 (MDD)
        portfolio_returns = [results['initial_capital']] + [p['value'] for p in portfolio_history]
        peak = portfolio_returns[0]
        mdd = 0

        for value in portfolio_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > mdd:
                mdd = drawdown

        print(f"\n📉 최대 낙폭 (MDD):")
        print(f"  - F-Score: {mdd:.2f}%")

        # 3. Sharpe Ratio (간이 버전)
        returns = [p['return'] for p in portfolio_history]
        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return > 0:
            sharpe = avg_return / std_return
        else:
            sharpe = 0

        print(f"\n⚖️  Sharpe Ratio (간이):")
        print(f"  - F-Score: {sharpe:.2f}")

        # 4. 승률
        win_count = sum(1 for p in portfolio_history if p['return'] > 0)
        win_rate = win_count / len(portfolio_history) * 100

        print(f"\n🎯 승률:")
        print(f"  - {win_count}/{len(portfolio_history)}기간 ({win_rate:.1f}%)")

        print(f"\n{'='*60}\n")

        metrics = {
            'cagr': cagr,
            'kospi_cagr': kospi_cagr,
            'mdd': mdd,
            'sharpe': sharpe,
            'win_rate': win_rate
        }

        return metrics

    def save_results(self, results, metrics, filename=None):
        """결과 저장"""
        if filename is None:
            today = datetime.now().strftime('%Y%m%d')
            filename = f'backtest_results_{today}.csv'

        # 포트폴리오 히스토리 저장
        df_portfolio = pd.DataFrame(results['portfolio_history'])
        df_kospi = pd.DataFrame(results['kospi_history'])

        df_combined = pd.merge(df_portfolio, df_kospi, on='date', suffixes=('_portfolio', '_kospi'))

        df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 결과 저장: {filename}")

        # 요약 리포트
        summary_file = filename.replace('.csv', '_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("F-Score 백테스팅 결과 요약\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"기간: {self.start_date} ~ {self.end_date}\n")
            f.write(f"초기 자본: {results['initial_capital']:,}원\n\n")
            f.write(f"최종 결과:\n")
            f.write(f"  - F-Score 전략: {results['final_value']:,.0f}원 ({results['total_return']:+.2f}%)\n")
            f.write(f"  - KOSPI 벤치마크: {results['kospi_final_value']:,.0f}원 ({results['kospi_total_return']:+.2f}%)\n")
            f.write(f"  - 초과 수익: {results['excess_return']:+.2f}%p\n\n")
            f.write(f"성과 지표:\n")
            f.write(f"  - CAGR: {metrics['cagr']:.2f}%\n")
            f.write(f"  - MDD: {metrics['mdd']:.2f}%\n")
            f.write(f"  - Sharpe Ratio: {metrics['sharpe']:.2f}\n")
            f.write(f"  - 승률: {metrics['win_rate']:.1f}%\n")

        print(f"📄 요약 저장: {summary_file}\n")


def main():
    """메인 실행"""
    print("=" * 60)
    print("🚀 F-Score 백테스팅 시스템")
    print("=" * 60)

    # 1. 백테스터 초기화 (2021년 ~ 2024년)
    backtester = FScoreBacktester(
        start_date='20210101',
        end_date='20241031'
    )

    # 2. 백테스팅 실행 (6점 만점 종목, 최대 30개)
    results = backtester.simulate_portfolio(
        candidates_file='fscore_parallel_results_20251101.csv',
        min_score=6,
        max_stocks=30
    )

    if results:
        # 3. 성과 지표 계산
        metrics = backtester.calculate_metrics(results)

        # 4. 결과 저장
        backtester.save_results(results, metrics)

        print("\n✅ 백테스팅 완료!")


if __name__ == "__main__":
    main()
