"""
기술적 분석용 차트 데이터 수집 모듈

pykrx를 사용하여 주가 및 거래량 데이터 수집
"""

import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import time


class TechnicalDataCollector:
    """기술적 분석용 데이터 수집기"""

    def __init__(self, days=120, request_delay=0.1):
        """
        Parameters:
        -----------
        days : int
            수집할 과거 데이터 일수 (기본: 120일)
        request_delay : float
            요청 간 대기 시간(초) - 레이트 리밋 방지 (기본: 0.1초)
        """
        self.days = days
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days)
        self.request_delay = request_delay

    def get_ohlcv(self, ticker, max_retries=2):
        """
        종목의 OHLCV 데이터 수집 (재시도 포함)

        Parameters:
        -----------
        ticker : str
            6자리 종목 코드
        max_retries : int
            최대 재시도 횟수 (기본: 2)

        Returns:
        --------
        df : DataFrame
            OHLCV 데이터 (Open, High, Low, Close, Volume)
            컬럼: 시가, 고가, 저가, 종가, 거래량
        """
        start_str = self.start_date.strftime('%Y%m%d')
        end_str = self.end_date.strftime('%Y%m%d')

        for attempt in range(max_retries):
            try:
                # 레이트 리밋 방지 대기
                if self.request_delay > 0:
                    time.sleep(self.request_delay)

                # pykrx로 데이터 수집
                df = stock.get_market_ohlcv_by_date(start_str, end_str, ticker)

                if df is None or len(df) == 0:
                    return None

                # 컬럼명 영문으로 변경
                df = df.rename(columns={
                    '시가': 'Open',
                    '고가': 'High',
                    '저가': 'Low',
                    '종가': 'Close',
                    '거래량': 'Volume'
                })

                # 인덱스를 datetime으로 변환
                df.index = pd.to_datetime(df.index)

                # 최소 데이터 수 체크 (60일 이상)
                if len(df) < 60:
                    return None

                return df

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 1  # 1초 대기
                    time.sleep(wait_time)
                else:
                    # 최종 실패는 조용히 None 반환 (너무 많은 로그 방지)
                    return None

        return None

    def get_ohlcv_batch(self, ticker_list, max_workers=10):
        """
        여러 종목의 OHLCV 데이터 일괄 수집

        Parameters:
        -----------
        ticker_list : list
            종목 코드 리스트
        max_workers : int
            병렬 처리 워커 수

        Returns:
        --------
        results : dict
            {ticker: DataFrame} 형태
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from threading import Lock

        results = {}
        lock = Lock()
        total = len(ticker_list)

        print(f"\n📊 차트 데이터 수집 시작 ({total}개 종목, 최근 {self.days}일)")

        def collect_single(ticker):
            df = self.get_ohlcv(ticker)
            return ticker, df

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(collect_single, ticker): ticker
                      for ticker in ticker_list}

            completed = 0
            for future in as_completed(futures):
                ticker, df = future.result()

                with lock:
                    if df is not None:
                        results[ticker] = df

                    completed += 1
                    if completed % 50 == 0 or completed == total:
                        print(f"  진행: {completed}/{total} "
                              f"(성공: {len(results)}개)")

        print(f"✅ 수집 완료: {len(results)}/{total}개")
        return results

    def get_market_cap(self, ticker):
        """
        시가총액 조회

        Parameters:
        -----------
        ticker : str
            종목 코드

        Returns:
        --------
        market_cap : int
            시가총액 (단위: 원)
        """
        try:
            today = datetime.now().strftime('%Y%m%d')
            df = stock.get_market_cap_by_ticker(today)

            if ticker in df.index:
                return df.loc[ticker, '시가총액']
            return None

        except Exception as e:
            return None

    def get_price_change(self, ticker, days=30):
        """
        특정 기간 동안의 가격 변화율

        Parameters:
        -----------
        ticker : str
            종목 코드
        days : int
            기간 (일)

        Returns:
        --------
        change_pct : float
            변화율 (%)
        """
        try:
            df = self.get_ohlcv(ticker)
            if df is None or len(df) < days:
                return None

            recent_close = df['Close'].iloc[-1]
            past_close = df['Close'].iloc[-days]

            change_pct = ((recent_close - past_close) / past_close) * 100
            return round(change_pct, 2)

        except Exception as e:
            return None


def main():
    """테스트"""
    print("📊 기술적 데이터 수집기 테스트\n")

    # 샘플 종목
    test_tickers = [
        '005930',  # 삼성전자
        '000660',  # SK하이닉스
        '207940',  # 삼성바이오로직스
    ]

    collector = TechnicalDataCollector(days=120)

    # 단일 종목 테스트
    print("=" * 60)
    print("단일 종목 테스트: 삼성전자")
    print("=" * 60)

    df = collector.get_ohlcv('005930')
    if df is not None:
        print(f"\n데이터 수: {len(df)}일")
        print(f"기간: {df.index[0].date()} ~ {df.index[-1].date()}")
        print(f"\n최근 5일 데이터:")
        print(df.tail())

        # 가격 변화율
        change_30d = collector.get_price_change('005930', 30)
        print(f"\n최근 30일 변화율: {change_30d}%")

    # 배치 테스트
    print("\n" + "=" * 60)
    print("배치 수집 테스트")
    print("=" * 60)

    results = collector.get_ohlcv_batch(test_tickers)

    print(f"\n수집 결과:")
    for ticker, df in results.items():
        if df is not None:
            name = stock.get_market_ticker_name(ticker)
            print(f"  {name} ({ticker}): {len(df)}일 데이터")


if __name__ == "__main__":
    main()
