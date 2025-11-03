"""
주식 스크리너 모듈
KRX 전체 종목을 필터링하여 분석 대상 축소
2600개 → 300-500개
"""

import pandas as pd
from pykrx import stock
from datetime import datetime


class StockScreener:
    """주식 필터링 클래스"""

    def __init__(self):
        self.df_krx = None

    def get_all_tickers(self):
        """
        KRX 전체 종목 가져오기

        pykrx 사용 - 종목 코드와 이름만 빠르게 수집
        상세 정보(시총, 거래량)는 나중에 FnGuide에서 수집
        """
        print("📊 KRX 전체 종목 리스트 수집 중...")

        today = datetime.now().strftime('%Y%m%d')

        # KOSPI + KOSDAQ 종목 리스트
        kospi_tickers = stock.get_market_ticker_list(today, market="KOSPI")
        kosdaq_tickers = stock.get_market_ticker_list(today, market="KOSDAQ")

        # 종목 정보 수집 (코드와 이름만)
        ticker_list = []

        print(f"  KOSPI 종목 수집 중... ({len(kospi_tickers)}개)")
        for ticker in kospi_tickers:
            try:
                name = stock.get_market_ticker_name(ticker)
                ticker_list.append({
                    'Code': ticker,
                    'Name': name,
                    'Market': 'KOSPI'
                })
            except:
                pass

        print(f"  KOSDAQ 종목 수집 중... ({len(kosdaq_tickers)}개)")
        for ticker in kosdaq_tickers:
            try:
                name = stock.get_market_ticker_name(ticker)
                ticker_list.append({
                    'Code': ticker,
                    'Name': name,
                    'Market': 'KOSDAQ'
                })
            except:
                pass

        self.df_krx = pd.DataFrame(ticker_list)
        print(f"✅ 총 {len(self.df_krx)}개 종목 조회 완료")
        return self.df_krx

    def apply_basic_filters(self, df=None):
        """
        기본 필터링 (이름 기반)

        Parameters:
        -----------
        df : DataFrame
            필터링할 데이터프레임

        Returns:
        --------
        df_filtered : DataFrame
            필터링된 종목 리스트
        """
        if df is None:
            df = self.df_krx

        print(f"\n🔍 기본 필터링 적용 중...")
        original_count = len(df)

        df_filtered = df.copy()

        # 1. 우선주 제외
        df_filtered = df_filtered[~df_filtered['Name'].str.contains('우', na=False)].copy()
        print(f"  우선주 제외: {len(df_filtered)}개 (제외: {original_count - len(df_filtered)}개)")

        # 2. SPAC 제외
        df_filtered = df_filtered[~df_filtered['Name'].str.contains('스팩', na=False)].copy()
        df_filtered = df_filtered[~df_filtered['Name'].str.contains('제[0-9]+호', na=False, regex=True)].copy()
        print(f"  SPAC 제외: {len(df_filtered)}개")

        # 3. ETF, ETN 제외 (이름으로 판별)
        df_filtered = df_filtered[~df_filtered['Name'].str.contains('ETF|ETN', na=False, case=False)].copy()
        print(f"  ETF/ETN 제외: {len(df_filtered)}개")

        # 4. 리츠, 펀드 제외
        df_filtered = df_filtered[~df_filtered['Name'].str.contains('리츠|REIT|펀드', na=False, case=False)].copy()
        print(f"  리츠/펀드 제외: {len(df_filtered)}개")

        # 5. 관리종목 제외 (종목명에 표시되는 경우)
        df_filtered = df_filtered[~df_filtered['Name'].str.contains('관리', na=False)].copy()
        print(f"  관리종목 제외: {len(df_filtered)}개")

        print(f"\n✅ 필터링 완료: {original_count}개 → {len(df_filtered)}개")

        return df_filtered

    def screen(self):
        """
        종합 스크리닝 실행

        Returns:
        --------
        df_filtered : DataFrame
            필터링된 종목 리스트
        """
        print("=" * 60)
        print("🎯 주식 스크리닝 시작")
        print("=" * 60)

        # 1. 전체 종목 가져오기
        df = self.get_all_tickers()

        # 2. 기본 필터
        df_filtered = self.apply_basic_filters(df)

        print("\n" + "=" * 60)
        print(f"🎉 스크리닝 완료: 최종 {len(df_filtered)}개 종목")
        print("=" * 60)

        return df_filtered

    def save(self, df, filename='filtered_tickers.csv'):
        """필터링된 종목 저장"""
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 저장 완료: {filename}")


def main():
    """테스트"""
    screener = StockScreener()

    # 스크리닝 실행
    df_filtered = screener.screen()

    # 결과 저장
    screener.save(df_filtered)

    # 샘플 출력
    print("\n📋 필터링된 종목 샘플 (상위 20개):")
    print(df_filtered[['Code', 'Name', 'Market']].head(20).to_string())

    print(f"\n\n📊 통계:")
    print(f"  - 총 종목 수: {len(df_filtered)}개")
    print(f"  - KOSPI: {len(df_filtered[df_filtered['Market'] == 'KOSPI'])}개")
    print(f"  - KOSDAQ: {len(df_filtered[df_filtered['Market'] == 'KOSDAQ'])}개")


if __name__ == "__main__":
    main()
