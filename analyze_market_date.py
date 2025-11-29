"""
특정 날짜의 시장 상황 분석 스크립트
"""

import sys
from datetime import datetime, timedelta
from data_handler import StockDataHandler
import pandas as pd

def analyze_market_on_date(target_date_str):
    """
    특정 날짜의 시장 상황 분석

    Parameters:
    -----------
    target_date_str : str
        분석할 날짜 (YYYY-MM-DD 형식)
    """
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')

    # 60일 전부터 데이터 수집
    start_date = (target_date - timedelta(days=90)).strftime('%Y%m%d')
    end_date = target_date.strftime('%Y%m%d')

    print("="*70)
    print(f"📊 시장 상황 분석: {target_date_str}")
    print("="*70)

    # KOSPI 지수 데이터
    print("\n🔍 KOSPI 지수 데이터 수집 중...")
    kospi_handler = StockDataHandler('1001', start_date, end_date, is_index=True)

    if kospi_handler.daily_data.empty:
        print("❌ KOSPI 데이터를 가져올 수 없습니다.")
        return

    df = kospi_handler.daily_data.copy()

    # 이동평균선 계산
    df['SMA_5'] = df['trade_price'].rolling(5).mean()
    df['SMA_20'] = df['trade_price'].rolling(20).mean()
    df['SMA_60'] = df['trade_price'].rolling(60).mean()

    # 해당 날짜 찾기
    if target_date_str not in df.index.astype(str):
        print(f"\n⚠️ {target_date_str}은 거래일이 아닙니다.")
        # 가장 가까운 이전 거래일 찾기
        df.index = pd.to_datetime(df.index)
        mask = df.index <= target_date
        if mask.any():
            actual_date = df[mask].index[-1]
            print(f"   → 직전 거래일: {actual_date.strftime('%Y-%m-%d')} 기준으로 분석\n")
        else:
            print("   → 분석 가능한 데이터가 없습니다.")
            return
    else:
        actual_date = pd.to_datetime(target_date_str)

    # 해당 날짜 데이터
    idx = df.index.get_loc(actual_date)
    row = df.iloc[idx]

    # 이전 데이터 (5일 전, 20일 전)
    prev_5 = df.iloc[max(0, idx-5)]
    prev_20 = df.iloc[max(0, idx-20)]

    print(f"\n📅 분석 기준일: {actual_date.strftime('%Y-%m-%d')}")
    print("="*70)

    # 1. 현재 상태
    print(f"\n💰 KOSPI 지수 정보")
    print(f"  현재가:  {row['trade_price']:,.2f}")
    print(f"  5일선:   {row['SMA_5']:,.2f}")
    print(f"  20일선:  {row['SMA_20']:,.2f}")
    print(f"  60일선:  {row['SMA_60']:,.2f}")

    # 2. 이동평균 배열 상태
    print(f"\n📊 이동평균 배열")
    current = row['trade_price']
    sma_5 = row['SMA_5']
    sma_20 = row['SMA_20']
    sma_60 = row['SMA_60']

    if sma_5 > sma_20 > sma_60:
        alignment = "정배열 (상승장) 🟢"
    elif sma_5 < sma_20 < sma_60:
        alignment = "역배열 (하락장) 🔴"
    else:
        alignment = "혼조 (중립) 🟡"

    print(f"  {alignment}")

    # 3. 현재가 vs 이동평균선
    print(f"\n🎯 현재가 위치")
    if current > sma_5:
        print(f"  ✅ 현재가 > 5일선  (+{(current/sma_5-1)*100:.2f}%)")
    else:
        print(f"  ❌ 현재가 < 5일선  ({(current/sma_5-1)*100:.2f}%)")

    if current > sma_20:
        print(f"  ✅ 현재가 > 20일선 (+{(current/sma_20-1)*100:.2f}%)")
    else:
        print(f"  ❌ 현재가 < 20일선 ({(current/sma_20-1)*100:.2f}%)")

    # 4. 단기 추세 (5일선 vs 20일선)
    print(f"\n📈 단기 추세 (5일선 vs 20일선)")
    if sma_5 > sma_20:
        gap = (sma_5/sma_20 - 1) * 100
        print(f"  ✅ 5일선 > 20일선 (+{gap:.2f}%) - 단기 상승 추세")
    else:
        gap = (sma_5/sma_20 - 1) * 100
        print(f"  ❌ 5일선 < 20일선 ({gap:.2f}%) - 단기 하락 추세")

    # 5. 중기 추세 (20일선 기울기)
    print(f"\n📉 중기 추세 (20일선 변화)")
    if idx >= 5:
        sma_20_prev = df.iloc[idx-5]['SMA_20']
        slope = (sma_20 / sma_20_prev - 1) * 100
        if slope > 0.5:
            print(f"  ✅ 20일선 상승 중 (+{slope:.2f}% / 5일)")
        elif slope < -0.5:
            print(f"  ❌ 20일선 하락 중 ({slope:.2f}% / 5일)")
        else:
            print(f"  ⚠️ 20일선 보합 ({slope:.2f}% / 5일)")

    # 6. 최근 크로스 발생 체크
    print(f"\n🔄 최근 크로스 발생 (지난 10일)")
    cross_detected = False
    for i in range(max(0, idx-10), idx):
        prev_row = df.iloc[i]
        curr_row = df.iloc[i+1]

        # 골든크로스 (5일선이 20일선 상향 돌파)
        if prev_row['SMA_5'] <= prev_row['SMA_20'] and curr_row['SMA_5'] > curr_row['SMA_20']:
            days_ago = idx - (i+1)
            cross_date = df.index[i+1].strftime('%Y-%m-%d')
            print(f"  🟢 골든크로스: {cross_date} ({days_ago}일 전)")
            cross_detected = True

        # 데드크로스 (5일선이 20일선 하향 이탈)
        if prev_row['SMA_5'] >= prev_row['SMA_20'] and curr_row['SMA_5'] < curr_row['SMA_20']:
            days_ago = idx - (i+1)
            cross_date = df.index[i+1].strftime('%Y-%m-%d')
            print(f"  🔴 데드크로스: {cross_date} ({days_ago}일 전)")
            cross_detected = True

    if not cross_detected:
        print(f"  ⚪ 크로스 없음 (현재 상태 유지)")

    # 7. 시장 점수 계산
    print(f"\n🎯 시장 점수 (-3 ~ +3)")
    market_score = 0

    if current > sma_5:
        market_score += 1
        print(f"  +1: 현재가 > 5일선")
    else:
        market_score -= 1
        print(f"  -1: 현재가 < 5일선")

    if sma_5 > sma_20:
        market_score += 1
        print(f"  +1: 5일선 > 20일선")
    else:
        market_score -= 1
        print(f"  -1: 5일선 < 20일선")

    if idx >= 5:
        sma_20_prev = df.iloc[idx-5]['SMA_20']
        slope = (sma_20 / sma_20_prev - 1) * 100
        if slope > 0.5:
            market_score += 1
            print(f"  +1: 20일선 상승 중")
        elif slope < -0.5:
            market_score -= 1
            print(f"  -1: 20일선 하락 중")
        else:
            print(f"   0: 20일선 보합")

    print(f"\n  총점: {market_score}/3")

    # 8. 최종 판정
    print(f"\n" + "="*70)
    print(f"📋 최종 판정")
    print("="*70)

    if market_score >= 2:
        verdict = "🟢 시장 강세 - 적극 매수 가능"
    elif market_score >= 1:
        verdict = "🟡 시장 약세 - 선별 매수 (고득점 종목만)"
    elif market_score >= -1:
        verdict = "🟠 시장 혼조 - 신중한 관망 권장"
    else:
        verdict = "🔴 시장 약세 - 매수 중단 권장"

    print(f"\n{verdict}")

    # 9. 전후 비교 (참고)
    print(f"\n" + "="*70)
    print(f"📊 최근 10일간 추이")
    print("="*70)

    recent_10 = df.iloc[max(0, idx-10):idx+1][['trade_price', 'SMA_5', 'SMA_20']].tail(11)
    recent_10['Date'] = recent_10.index.strftime('%Y-%m-%d')
    recent_10['5vs20'] = recent_10['SMA_5'] > recent_10['SMA_20']

    print(recent_10[['Date', 'trade_price', 'SMA_5', 'SMA_20', '5vs20']].to_string(index=False))

    # 10. KOSDAQ도 확인
    print(f"\n" + "="*70)
    print(f"📊 KOSDAQ 지수 (참고)")
    print("="*70)

    kosdaq_handler = StockDataHandler('2001', start_date, end_date, is_index=True)

    if not kosdaq_handler.daily_data.empty:
        df_kosdaq = kosdaq_handler.daily_data.copy()
        df_kosdaq['SMA_5'] = df_kosdaq['trade_price'].rolling(5).mean()
        df_kosdaq['SMA_20'] = df_kosdaq['trade_price'].rolling(20).mean()

        if actual_date in df_kosdaq.index:
            kosdaq_row = df_kosdaq.loc[actual_date]
            print(f"  현재가:  {kosdaq_row['trade_price']:,.2f}")
            print(f"  5일선:   {kosdaq_row['SMA_5']:,.2f}")
            print(f"  20일선:  {kosdaq_row['SMA_20']:,.2f}")

            if kosdaq_row['SMA_5'] > kosdaq_row['SMA_20']:
                print(f"  상태: 단기 상승 추세 ✅")
            else:
                print(f"  상태: 단기 하락 추세 ❌")

if __name__ == "__main__":
    # 2024-11-09 분석
    analyze_market_on_date('2024-11-09')
