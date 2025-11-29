"""
시장 필터 모듈

시장 전체의 추세를 판단하여 매수/매도 타이밍 결정
- 하락장에서는 아무리 좋은 종목도 매수 금지
- 상승장에서만 적극 매수
"""

from datetime import datetime, timedelta
from data_handler import StockDataHandler
import pandas as pd


class MarketFilter:
    """
    시장 추세 필터

    KOSPI/KOSDAQ 지수를 분석하여 시장 상태 판단
    """

    def __init__(self, index_code='1001', days=120):
        """
        Parameters:
        -----------
        index_code : str
            지수 코드 (1001=KOSPI, 2001=KOSDAQ)
        days : int
            분석할 일수 (기본: 120일)
        """
        self.index_code = index_code
        self.days = days
        self.index_name = 'KOSPI' if index_code == '1001' else 'KOSDAQ'
        self.df = None
        self.score = None
        self.regime = None
        self.details = []

    def load_data(self, end_date=None):
        """
        지수 데이터 로드

        Parameters:
        -----------
        end_date : str
            종료일 (YYYY-MM-DD), None이면 오늘
        """
        if end_date is None:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        start_date = end_date - timedelta(days=self.days + 30)  # 여유분

        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        handler = StockDataHandler(
            self.index_code,
            start_str,
            end_str,
            is_index=True
        )

        if handler.daily_data.empty:
            raise ValueError(f"{self.index_name} 데이터를 가져올 수 없습니다")

        self.df = handler.daily_data.copy()

        # 이동평균선 계산
        self.df['SMA_5'] = self.df['trade_price'].rolling(5).mean()
        self.df['SMA_20'] = self.df['trade_price'].rolling(20).mean()
        self.df['SMA_60'] = self.df['trade_price'].rolling(60).mean()

        return self.df

    def calculate_market_score(self):
        """
        시장 점수 계산 (-3 ~ +3)

        체크 항목:
        1. 현재가 vs 5일선 (+1/-1)
        2. 5일선 vs 20일선 (+1/-1)
        3. 20일선 기울기 (+1/-1)

        Returns:
        --------
        score : int
            -3 (최악) ~ +3 (최고)
        details : list
            상세 판단 내용
        """
        if self.df is None or len(self.df) < 20:
            raise ValueError("데이터를 먼저 로드하세요 (load_data)")

        # 최신 데이터
        current = self.df['trade_price'].iloc[-1]
        sma_5 = self.df['SMA_5'].iloc[-1]
        sma_20 = self.df['SMA_20'].iloc[-1]

        # 5일 전 20일선 (기울기 계산용)
        if len(self.df) >= 5:
            sma_20_prev = self.df['SMA_20'].iloc[-6]
        else:
            sma_20_prev = sma_20

        score = 0
        details = []

        # 1. 현재가 vs 5일선
        if current > sma_5:
            score += 1
            gap = (current / sma_5 - 1) * 100
            details.append(f"✅ 현재가 > 5일선 (+{gap:.2f}%)")
        else:
            score -= 1
            gap = (current / sma_5 - 1) * 100
            details.append(f"❌ 현재가 < 5일선 ({gap:.2f}%)")

        # 2. 5일선 vs 20일선 (단기 추세)
        if sma_5 > sma_20:
            score += 1
            gap = (sma_5 / sma_20 - 1) * 100
            details.append(f"✅ 5일선 > 20일선 (+{gap:.2f}%)")
        else:
            score -= 1
            gap = (sma_5 / sma_20 - 1) * 100
            details.append(f"❌ 5일선 < 20일선 ({gap:.2f}%)")

        # 3. 20일선 기울기 (중기 추세)
        slope = (sma_20 / sma_20_prev - 1) * 100
        if slope > 0.5:  # 5일간 0.5% 이상 상승
            score += 1
            details.append(f"✅ 20일선 상승 중 (+{slope:.2f}% / 5일)")
        elif slope < -0.5:  # 5일간 0.5% 이상 하락
            score -= 1
            details.append(f"❌ 20일선 하락 중 ({slope:.2f}% / 5일)")
        else:
            details.append(f"⚠️ 20일선 보합 ({slope:.2f}% / 5일)")

        self.score = score
        self.details = details

        return score, details

    def detect_cross(self, lookback=10):
        """
        최근 골든크로스/데드크로스 감지

        Parameters:
        -----------
        lookback : int
            최근 며칠 내 크로스 체크

        Returns:
        --------
        cross_type : str
            'golden_cross', 'dead_cross', 'none'
        days_ago : int or None
            크로스 발생 일수
        """
        if self.df is None:
            raise ValueError("데이터를 먼저 로드하세요")

        recent = self.df.tail(lookback + 1)

        # 골든크로스 감지
        for i in range(1, len(recent)):
            prev_below = recent['SMA_5'].iloc[i-1] <= recent['SMA_20'].iloc[i-1]
            curr_above = recent['SMA_5'].iloc[i] > recent['SMA_20'].iloc[i]

            if prev_below and curr_above:
                days_ago = len(recent) - 1 - i
                return 'golden_cross', days_ago

        # 데드크로스 감지
        for i in range(1, len(recent)):
            prev_above = recent['SMA_5'].iloc[i-1] >= recent['SMA_20'].iloc[i-1]
            curr_below = recent['SMA_5'].iloc[i] < recent['SMA_20'].iloc[i]

            if prev_above and curr_below:
                days_ago = len(recent) - 1 - i
                return 'dead_cross', days_ago

        return 'none', None

    def determine_regime(self):
        """
        시장 체제 판단

        Returns:
        --------
        regime : str
            'strong_bull', 'bull', 'neutral', 'bear', 'strong_bear'
        """
        if self.score is None:
            self.calculate_market_score()

        if self.score >= 2:
            regime = 'strong_bull'
        elif self.score == 1:
            regime = 'bull'
        elif self.score == 0:
            regime = 'neutral'
        elif self.score == -1:
            regime = 'bear'
        else:  # -2 or -3
            regime = 'strong_bear'

        self.regime = regime
        return regime

    def should_trade(self, min_score=0):
        """
        거래 허용 여부 판단

        Parameters:
        -----------
        min_score : int
            최소 요구 점수 (기본: 0)

        Returns:
        --------
        allowed : bool
            True면 거래 허용, False면 중단
        reason : str
            판단 이유
        """
        if self.score is None:
            self.calculate_market_score()

        if self.regime is None:
            self.determine_regime()

        if self.score >= min_score:
            return True, f"시장 점수 {self.score}/3 (기준: {min_score} 이상) ✅"
        else:
            return False, f"시장 점수 {self.score}/3 (기준: {min_score} 이상 필요) ❌"

    def get_trading_strategy(self):
        """
        시장 상황에 맞는 거래 전략 제안

        Returns:
        --------
        strategy : dict
            권장 전략 (min_fscore, min_timing, max_stocks 등)
        """
        if self.regime is None:
            self.determine_regime()

        strategies = {
            'strong_bull': {
                'action': 'aggressive_buy',
                'min_fscore': 4,
                'min_timing': 5,
                'max_stocks': 20,
                'description': '🟢 적극 매수 - 시장 강세',
                'portfolio': '공격형 포트폴리오 (성장주 포함)'
            },
            'bull': {
                'action': 'buy',
                'min_fscore': 5,
                'min_timing': 6,
                'max_stocks': 15,
                'description': '🟡 선별 매수 - 시장 약한 상승',
                'portfolio': '균형형 포트폴리오 (우량주 중심)'
            },
            'neutral': {
                'action': 'selective_buy',
                'min_fscore': 6,
                'min_timing': 7,
                'max_stocks': 10,
                'description': '🟠 신중한 매수 - 시장 혼조',
                'portfolio': '보수형 포트폴리오 (고득점만)'
            },
            'bear': {
                'action': 'hold',
                'min_fscore': 7,
                'min_timing': 8,
                'max_stocks': 5,
                'description': '🔴 관망 권장 - 시장 약세',
                'portfolio': '방어주만 극소량 (대형 우량주)'
            },
            'strong_bear': {
                'action': 'no_trade',
                'min_fscore': 9,
                'min_timing': 9,
                'max_stocks': 0,
                'description': '⛔ 매수 중단 - 시장 강한 하락',
                'portfolio': '현금 보유 또는 인버스 ETF 검토'
            }
        }

        return strategies[self.regime]

    def print_report(self):
        """
        시장 상황 리포트 출력
        """
        if self.df is None:
            raise ValueError("데이터를 먼저 로드하세요")

        if self.score is None:
            self.calculate_market_score()

        if self.regime is None:
            self.determine_regime()

        # 크로스 감지
        cross_type, days_ago = self.detect_cross()

        # 전략 가져오기
        strategy = self.get_trading_strategy()

        print("="*70)
        print(f"📊 {self.index_name} 시장 필터 분석")
        print("="*70)

        # 기본 정보
        current_date = self.df.index[-1]
        current_price = self.df['trade_price'].iloc[-1]
        sma_5 = self.df['SMA_5'].iloc[-1]
        sma_20 = self.df['SMA_20'].iloc[-1]

        print(f"\n📅 분석 기준일: {current_date}")
        print(f"💰 {self.index_name} 지수: {current_price:,.2f}")
        print(f"   5일선:  {sma_5:,.2f}")
        print(f"   20일선: {sma_20:,.2f}")

        # 점수 및 상세
        print(f"\n🎯 시장 점수: {self.score}/3")
        for detail in self.details:
            print(f"   {detail}")

        # 크로스 정보
        print(f"\n🔄 최근 크로스 (10일 이내)")
        if cross_type == 'golden_cross':
            print(f"   🟢 골든크로스 발생 ({days_ago}일 전)")
        elif cross_type == 'dead_cross':
            print(f"   🔴 데드크로스 발생 ({days_ago}일 전)")
        else:
            print(f"   ⚪ 크로스 없음 (현재 상태 유지)")

        # 최종 판정
        print(f"\n" + "="*70)
        print(f"📋 최종 판정")
        print("="*70)
        print(f"\n{strategy['description']}")
        print(f"\n권장 전략:")
        print(f"  - 행동: {strategy['action']}")
        print(f"  - 최소 F-Score: {strategy['min_fscore']}점")
        print(f"  - 최소 타이밍: {strategy['min_timing']}점")
        print(f"  - 최대 종목 수: {strategy['max_stocks']}개")
        print(f"  - 포트폴리오: {strategy['portfolio']}")
        print()

        return strategy


def quick_check(index_code='1001', min_score=0):
    """
    빠른 시장 체크 (간편 함수)

    Parameters:
    -----------
    index_code : str
        1001=KOSPI, 2001=KOSDAQ
    min_score : int
        최소 요구 점수

    Returns:
    --------
    allowed : bool
        거래 허용 여부
    market_score : int
        시장 점수
    """
    filter = MarketFilter(index_code)
    filter.load_data()
    score, _ = filter.calculate_market_score()
    allowed, _ = filter.should_trade(min_score)

    return allowed, score


if __name__ == "__main__":
    # 테스트
    print("KOSPI 시장 필터 테스트\n")

    kospi = MarketFilter('1001')
    kospi.load_data()
    strategy = kospi.print_report()

    print("\n" + "="*70)
    print("KOSDAQ 시장 필터 테스트\n")

    kosdaq = MarketFilter('2001')
    kosdaq.load_data()
    strategy = kosdaq.print_report()
