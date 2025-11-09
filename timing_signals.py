"""
타이밍 신호 검출 모듈

기술적 지표를 바탕으로 매수/매도 타이밍 판별
"""

import pandas as pd
import numpy as np


class TimingSignals:
    """타이밍 신호 검출기"""

    def __init__(self, df):
        """
        Parameters:
        -----------
        df : DataFrame
            기술적 지표가 포함된 데이터프레임
        """
        self.df = df
        self.signals = {}
        self.score = 0
        self.details = []

    def check_golden_cross(self, lookback=5):
        """
        골든크로스 체크 (20일선이 60일선 상향 돌파)

        Parameters:
        -----------
        lookback : int
            최근 며칠 이내 발생했는지 체크 (기본: 5일)

        Returns:
        --------
        signal : dict
            {'detected': bool, 'score': int, 'description': str}
        """
        if 'SMA_20' not in self.df or 'SMA_60' not in self.df:
            return {'detected': False, 'score': 0, 'description': '데이터 부족'}

        # 최근 데이터
        recent = self.df.tail(lookback)

        # 현재 20일선이 60일선 위에 있는가?
        current_above = recent['SMA_20'].iloc[-1] > recent['SMA_60'].iloc[-1]

        # 과거에는 아래에 있었는가?
        past_below = recent['SMA_20'].iloc[0] <= recent['SMA_60'].iloc[0]

        # 골든크로스 발생
        if current_above and past_below:
            score = 2
            detected = True
            desc = f"골든크로스 발생 (최근 {lookback}일 이내) ⭐"
        # 이미 골든크로스 상태 유지
        elif current_above:
            score = 1
            detected = True
            desc = "20일선 > 60일선 (상승 추세)"
        else:
            score = 0
            detected = False
            desc = "20일선 < 60일선 (하락 또는 횡보)"

        signal = {
            'detected': detected,
            'score': score,
            'description': desc
        }

        self.signals['golden_cross'] = signal
        if detected:
            self.score += score
            self.details.append(desc)

        return signal

    def check_ma_alignment(self):
        """
        이동평균 정배열 체크 (5일 > 20일 > 60일)

        Returns:
        --------
        signal : dict
            {'detected': bool, 'score': int, 'description': str}
        """
        if not all(col in self.df for col in ['SMA_5', 'SMA_20', 'SMA_60']):
            return {'detected': False, 'score': 0, 'description': '데이터 부족'}

        ma5 = self.df['SMA_5'].iloc[-1]
        ma20 = self.df['SMA_20'].iloc[-1]
        ma60 = self.df['SMA_60'].iloc[-1]

        # 완전 정배열
        if ma5 > ma20 > ma60:
            score = 1
            detected = True
            desc = "이동평균 정배열 (5>20>60)"
        # 부분 정배열
        elif ma5 > ma20:
            score = 0.5
            detected = True
            desc = "단기 정배열 (5>20)"
        else:
            score = 0
            detected = False
            desc = "정배열 아님"

        signal = {
            'detected': detected,
            'score': score,
            'description': desc
        }

        self.signals['ma_alignment'] = signal
        if detected:
            self.score += score
            self.details.append(desc)

        return signal

    def check_rsi(self):
        """
        RSI 구간 체크

        Returns:
        --------
        signal : dict
            {'detected': bool, 'score': int, 'description': str}
        """
        if 'RSI' not in self.df:
            return {'detected': False, 'score': 0, 'description': '데이터 부족'}

        rsi = self.df['RSI'].iloc[-1]

        if pd.isna(rsi):
            return {'detected': False, 'score': 0, 'description': 'RSI 계산 불가'}

        # RSI 30~70 구간 (정상 범위)
        if 30 <= rsi <= 70:
            score = 1
            detected = True

            # 세부 구간
            if 40 <= rsi <= 60:
                desc = f"RSI {rsi:.1f} (중립 구간)"
            elif 30 <= rsi < 40:
                desc = f"RSI {rsi:.1f} (과매도 탈출)"
            else:  # 60 < rsi <= 70
                desc = f"RSI {rsi:.1f} (상승 모멘텀)"

        # RSI 50 돌파 (추가 점수)
        elif 50 < rsi <= 55:
            score = 1.5
            detected = True
            desc = f"RSI {rsi:.1f} (50선 돌파 ⭐)"

        # RSI 과매수 (70 이상)
        elif rsi > 70:
            score = 0
            detected = False
            desc = f"RSI {rsi:.1f} (과매수, 조정 가능성)"

        # RSI 과매도 (30 이하)
        else:
            score = 0
            detected = False
            desc = f"RSI {rsi:.1f} (과매도, 리스크)"

        signal = {
            'detected': detected,
            'score': score,
            'description': desc,
            'value': rsi
        }

        self.signals['rsi'] = signal
        if detected:
            self.score += score
            self.details.append(desc)

        return signal

    def check_macd(self):
        """
        MACD 신호 체크

        Returns:
        --------
        signal : dict
            {'detected': bool, 'score': int, 'description': str}
        """
        if 'MACD' not in self.df or 'MACD_signal' not in self.df:
            return {'detected': False, 'score': 0, 'description': '데이터 부족'}

        macd = self.df['MACD'].iloc[-1]
        macd_signal = self.df['MACD_signal'].iloc[-1]
        macd_hist = self.df['MACD_histogram'].iloc[-1]

        if pd.isna(macd) or pd.isna(macd_signal):
            return {'detected': False, 'score': 0, 'description': 'MACD 계산 불가'}

        # MACD > Signal (매수 신호)
        if macd > macd_signal:
            # MACD 히스토그램 양수 (강한 신호)
            if macd_hist > 0:
                score = 2
                desc = "MACD > Signal & 양전환 ⭐⭐"
            else:
                score = 1
                desc = "MACD > Signal"

            detected = True

        # MACD가 0선 위 (추가 가점)
        elif macd > 0:
            score = 0.5
            detected = True
            desc = "MACD 0선 위 (상승 추세)"

        else:
            score = 0
            detected = False
            desc = "MACD < Signal (약세)"

        signal = {
            'detected': detected,
            'score': score,
            'description': desc,
            'macd': macd,
            'signal': macd_signal
        }

        self.signals['macd'] = signal
        if detected:
            self.score += score
            self.details.append(desc)

        return signal

    def check_volume(self):
        """
        거래량 급증 체크

        Returns:
        --------
        signal : dict
            {'detected': bool, 'score': int, 'description': str}
        """
        if 'Volume_ratio' not in self.df:
            return {'detected': False, 'score': 0, 'description': '데이터 부족'}

        volume_ratio = self.df['Volume_ratio'].iloc[-1]

        if pd.isna(volume_ratio):
            return {'detected': False, 'score': 0, 'description': '거래량 계산 불가'}

        # 거래량 2배 이상 (강한 신호)
        if volume_ratio >= 2.0:
            score = 1.5
            detected = True
            desc = f"거래량 급증 ({volume_ratio:.1f}배) ⭐"

        # 거래량 1.5배 이상
        elif volume_ratio >= 1.5:
            score = 1
            detected = True
            desc = f"거래량 증가 ({volume_ratio:.1f}배)"

        # 정상 범위
        elif volume_ratio >= 0.8:
            score = 0.5
            detected = True
            desc = f"거래량 정상 ({volume_ratio:.1f}배)"

        # 거래량 감소
        else:
            score = 0
            detected = False
            desc = f"거래량 부진 ({volume_ratio:.1f}배)"

        signal = {
            'detected': detected,
            'score': score,
            'description': desc,
            'ratio': volume_ratio
        }

        self.signals['volume'] = signal
        if detected:
            self.score += score
            self.details.append(desc)

        return signal

    def check_bollinger_bounce(self):
        """
        볼린저 밴드 하단 반등 체크

        Returns:
        --------
        signal : dict
            {'detected': bool, 'score': int, 'description': str}
        """
        if not all(col in self.df for col in ['Close', 'BB_lower', 'BB_middle', 'BB_upper']):
            return {'detected': False, 'score': 0, 'description': '데이터 부족'}

        close = self.df['Close'].iloc[-1]
        bb_lower = self.df['BB_lower'].iloc[-1]
        bb_middle = self.df['BB_middle'].iloc[-1]
        bb_upper = self.df['BB_upper'].iloc[-1]

        # 하단 밴드 근처 (하단 ~ 하단+10% 사이)
        if bb_lower <= close <= bb_lower + (bb_middle - bb_lower) * 0.3:
            # 최근 3일 중 하단 터치 후 반등했는가?
            recent_lows = self.df['Low'].tail(3)
            touched_lower = any(low <= bb_lower * 1.02 for low in recent_lows)

            if touched_lower:
                score = 1
                detected = True
                desc = "볼린저 하단 반등 ⭐"
            else:
                score = 0.5
                detected = True
                desc = "볼린저 하단 근처"

        # 중심선 돌파
        elif close > bb_middle:
            score = 0.5
            detected = True
            desc = "볼린저 중심선 위"

        # 상단 밴드 근처 (과매수)
        elif close >= bb_upper * 0.98:
            score = 0
            detected = False
            desc = "볼린저 상단 근처 (과매수)"

        else:
            score = 0
            detected = False
            desc = "볼린저 중립"

        signal = {
            'detected': detected,
            'score': score,
            'description': desc
        }

        self.signals['bollinger'] = signal
        if detected:
            self.score += score
            self.details.append(desc)

        return signal

    def calculate_timing_score(self):
        """
        종합 타이밍 스코어 계산

        Returns:
        --------
        result : dict
            {
                'score': float (0~10점),
                'signals': dict,
                'rating': str,
                'recommendation': str
            }
        """
        # 모든 신호 체크
        self.score = 0
        self.details = []

        self.check_golden_cross()
        self.check_ma_alignment()
        self.check_rsi()
        self.check_macd()
        self.check_volume()
        self.check_bollinger_bounce()

        # 점수 정규화 (0~10점)
        max_score = 10
        normalized_score = min(self.score, max_score)

        # 등급 판정
        if normalized_score >= 7:
            rating = "A (매우 우수)"
            recommendation = "강력 매수 추천 ⭐⭐⭐"
        elif normalized_score >= 5:
            rating = "B (우수)"
            recommendation = "매수 고려 ⭐⭐"
        elif normalized_score >= 3:
            rating = "C (보통)"
            recommendation = "관망 ⭐"
        else:
            rating = "D (부진)"
            recommendation = "매수 보류"

        result = {
            'score': round(normalized_score, 2),
            'signals': self.signals,
            'details': self.details,
            'rating': rating,
            'recommendation': recommendation
        }

        return result

    def print_report(self):
        """타이밍 분석 리포트 출력"""
        result = self.calculate_timing_score()

        print("\n" + "=" * 60)
        print("타이밍 분석 리포트")
        print("=" * 60)

        print(f"\n📊 종합 점수: {result['score']:.2f}/10점")
        print(f"🏆 등급: {result['rating']}")
        print(f"💡 추천: {result['recommendation']}")

        print(f"\n📋 시그널 상세:")
        for key, signal in result['signals'].items():
            status = "✅" if signal['detected'] else "❌"
            print(f"  {status} {signal['description']} (+{signal['score']}점)")


def main():
    """테스트"""
    print("📊 타이밍 신호 검출 테스트\n")

    from technical_data_collector import TechnicalDataCollector
    from technical_indicators import TechnicalIndicators

    # 삼성전자 데이터
    collector = TechnicalDataCollector(days=120)
    df = collector.get_ohlcv('005930')

    if df is None:
        print("데이터 수집 실패")
        return

    # 지표 계산
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.calculate_all()

    # 타이밍 분석
    signals = TimingSignals(df_with_indicators)
    result = signals.calculate_timing_score()

    # 리포트 출력
    signals.print_report()


if __name__ == "__main__":
    main()
