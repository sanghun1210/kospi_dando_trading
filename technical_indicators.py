"""
기술적 지표 계산 모듈

pandas-ta를 사용한 주요 기술적 지표 계산
"""

import pandas as pd
import pandas_ta as ta


class TechnicalIndicators:
    """기술적 지표 계산기"""

    def __init__(self, df):
        """
        Parameters:
        -----------
        df : DataFrame
            OHLCV 데이터
            필수 컬럼: Open, High, Low, Close, Volume
        """
        self.df = df.copy()
        self.indicators = {}

    def calculate_moving_averages(self):
        """
        이동평균선 계산

        계산:
        - SMA 5, 20, 60, 120일

        Returns:
        --------
        ma_dict : dict
            {'SMA_5': Series, 'SMA_20': Series, ...}
        """
        periods = [5, 20, 60, 120]
        ma_dict = {}

        for period in periods:
            sma = ta.sma(self.df['Close'], length=period)
            ma_dict[f'SMA_{period}'] = sma
            self.df[f'SMA_{period}'] = sma

        self.indicators['moving_averages'] = ma_dict
        return ma_dict

    def calculate_rsi(self, period=14):
        """
        RSI (Relative Strength Index) 계산

        Parameters:
        -----------
        period : int
            RSI 기간 (기본: 14일)

        Returns:
        --------
        rsi : Series
            RSI 값 (0~100)
        """
        rsi = ta.rsi(self.df['Close'], length=period)
        self.df['RSI'] = rsi
        self.indicators['rsi'] = rsi
        return rsi

    def calculate_macd(self, fast=12, slow=26, signal=9):
        """
        MACD (Moving Average Convergence Divergence) 계산

        Parameters:
        -----------
        fast : int
            빠른 이동평균 기간 (기본: 12)
        slow : int
            느린 이동평균 기간 (기본: 26)
        signal : int
            시그널선 기간 (기본: 9)

        Returns:
        --------
        macd_dict : dict
            {'MACD': Series, 'MACD_signal': Series, 'MACD_histogram': Series}
        """
        macd_df = ta.macd(self.df['Close'], fast=fast, slow=slow, signal=signal)

        if macd_df is not None:
            # pandas-ta 0.4+ 버전 컬럼명
            macd_col = f'MACD_{fast}_{slow}_{signal}'
            signal_col = f'MACDs_{fast}_{slow}_{signal}'
            hist_col = f'MACDh_{fast}_{slow}_{signal}'

            macd_dict = {
                'MACD': macd_df[macd_col],
                'MACD_signal': macd_df[signal_col],
                'MACD_histogram': macd_df[hist_col]
            }

            self.df['MACD'] = macd_df[macd_col]
            self.df['MACD_signal'] = macd_df[signal_col]
            self.df['MACD_histogram'] = macd_df[hist_col]

            self.indicators['macd'] = macd_dict
            return macd_dict

        return None

    def calculate_bollinger_bands(self, period=20, std=2):
        """
        볼린저 밴드 계산

        Parameters:
        -----------
        period : int
            이동평균 기간 (기본: 20)
        std : int
            표준편차 배수 (기본: 2)

        Returns:
        --------
        bb_dict : dict
            {'BB_upper': Series, 'BB_middle': Series, 'BB_lower': Series}
        """
        bb_df = ta.bbands(self.df['Close'], length=period, std=std)

        if bb_df is not None:
            # pandas-ta 컬럼명
            lower_col = f'BBL_{period}_{std}.0_{std}.0'
            middle_col = f'BBM_{period}_{std}.0_{std}.0'
            upper_col = f'BBU_{period}_{std}.0_{std}.0'

            bb_dict = {
                'BB_upper': bb_df[upper_col],
                'BB_middle': bb_df[middle_col],
                'BB_lower': bb_df[lower_col]
            }

            self.df['BB_upper'] = bb_df[upper_col]
            self.df['BB_middle'] = bb_df[middle_col]
            self.df['BB_lower'] = bb_df[lower_col]

            self.indicators['bollinger_bands'] = bb_dict
            return bb_dict

        return None

    def calculate_volume_indicators(self):
        """
        거래량 지표 계산

        계산:
        - 거래량 이동평균 (20일)
        - 거래량 비율 (현재/평균)

        Returns:
        --------
        volume_dict : dict
            {'Volume_SMA': Series, 'Volume_ratio': Series}
        """
        volume_sma = ta.sma(self.df['Volume'], length=20)
        self.df['Volume_SMA'] = volume_sma

        # 거래량 비율 계산
        volume_ratio = self.df['Volume'] / volume_sma
        self.df['Volume_ratio'] = volume_ratio

        volume_dict = {
            'Volume_SMA': volume_sma,
            'Volume_ratio': volume_ratio
        }

        self.indicators['volume'] = volume_dict
        return volume_dict

    def calculate_all(self):
        """
        모든 지표 한번에 계산

        Returns:
        --------
        df : DataFrame
            모든 지표가 추가된 데이터프레임
        """
        print("  📊 기술적 지표 계산 중...")

        self.calculate_moving_averages()
        self.calculate_rsi()
        self.calculate_macd()
        self.calculate_bollinger_bands()
        self.calculate_volume_indicators()

        print("  ✅ 지표 계산 완료")
        return self.df

    def get_latest_values(self):
        """
        최신 지표 값 반환

        Returns:
        --------
        latest : dict
            최신 지표 값들
        """
        latest = {
            'Close': self.df['Close'].iloc[-1],
            'SMA_5': self.df['SMA_5'].iloc[-1] if 'SMA_5' in self.df else None,
            'SMA_20': self.df['SMA_20'].iloc[-1] if 'SMA_20' in self.df else None,
            'SMA_60': self.df['SMA_60'].iloc[-1] if 'SMA_60' in self.df else None,
            'SMA_120': self.df['SMA_120'].iloc[-1] if 'SMA_120' in self.df else None,
            'RSI': self.df['RSI'].iloc[-1] if 'RSI' in self.df else None,
            'MACD': self.df['MACD'].iloc[-1] if 'MACD' in self.df else None,
            'MACD_signal': self.df['MACD_signal'].iloc[-1] if 'MACD_signal' in self.df else None,
            'MACD_histogram': self.df['MACD_histogram'].iloc[-1] if 'MACD_histogram' in self.df else None,
            'Volume_ratio': self.df['Volume_ratio'].iloc[-1] if 'Volume_ratio' in self.df else None,
        }

        return latest


def main():
    """테스트"""
    print("📊 기술적 지표 계산 테스트\n")

    from technical_data_collector import TechnicalDataCollector

    # 삼성전자 데이터 수집
    collector = TechnicalDataCollector(days=120)
    df = collector.get_ohlcv('005930')

    if df is None:
        print("데이터 수집 실패")
        return

    print(f"수집된 데이터: {len(df)}일\n")

    # 지표 계산
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.calculate_all()

    # 최신 값 출력
    print("\n" + "=" * 60)
    print("최신 지표 값 (삼성전자)")
    print("=" * 60)

    latest = indicators.get_latest_values()

    print(f"\n현재가: {latest['Close']:,.0f}원")
    print(f"\n이동평균:")
    print(f"  5일선:  {latest['SMA_5']:,.0f}원")
    print(f"  20일선: {latest['SMA_20']:,.0f}원")
    print(f"  60일선: {latest['SMA_60']:,.0f}원")
    print(f"  120일선: {latest['SMA_120']:,.0f}원")

    print(f"\nRSI (14일): {latest['RSI']:.2f}")

    print(f"\nMACD:")
    print(f"  MACD: {latest['MACD']:.2f}")
    print(f"  Signal: {latest['MACD_signal']:.2f}")
    print(f"  Histogram: {latest['MACD_histogram']:.2f}")

    print(f"\n거래량:")
    print(f"  거래량 비율: {latest['Volume_ratio']:.2f}x")

    # 최근 5일 데이터
    print("\n" + "=" * 60)
    print("최근 5일 데이터")
    print("=" * 60)

    cols_to_show = ['Close', 'SMA_20', 'SMA_60', 'RSI', 'MACD', 'Volume_ratio']
    print(df_with_indicators[cols_to_show].tail().round(2))


if __name__ == "__main__":
    main()
