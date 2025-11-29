"""
텔레그램 알림 스크립트

GitHub Actions에서 분석 결과를 텔레그램으로 전송
"""

import argparse
import requests
import sys
from datetime import datetime


def send_telegram_message(token, chat_id, message, parse_mode='Markdown'):
    """텔레그램 메시지 전송"""
    url = f'https://api.telegram.org/bot{token}/sendMessage'

    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        print(f"✅ 텔레그램 메시지 전송 완료")
        return True
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        return False


def format_morning_message(market_score, verdict, golden_cross):
    """아침 시장 체크 메시지 포맷"""

    date = datetime.now().strftime('%Y-%m-%d')

    # 시장 점수 변환 (빈 문자열 또는 None 처리)
    try:
        score = int(market_score) if market_score and market_score != '' else 0
    except (ValueError, TypeError):
        score = 0
        market_score = "0"

    # 이모지 선택
    if score >= 2:
        emoji = "🟢"
    elif score >= 0:
        emoji = "🟡"
    else:
        emoji = "🔴"

    message = f"""
🌅 *아침 시장 체크* ({date})

{emoji} *시장 점수: {market_score}/3*

*판정:* {verdict}
"""

    if golden_cross:
        message += f"\n{golden_cross}\n"

    # 매수 전략 (score는 위에서 이미 계산됨)
    if score >= 2:
        message += """
💰 *오늘 매수 전략*
✅ 적극 매수 가능
→ 어제 저녁 분석 상위 종목 매수
"""
    elif score >= 0:
        message += """
💰 *오늘 매수 전략*
⚠️ 신중하게 선별 매수
→ 고득점 종목만 소량 매수
"""
    else:
        message += """
💰 *오늘 매수 전략*
🛑 매수 대기 권장
→ 현금 보유 또는 관망
"""

    message += "\n📊 상세 분석은 저녁 6시 결과 참고"

    return message


def format_evening_message(market_score, should_run, total_stocks, run_url):
    """저녁 전체 분석 메시지 포맷"""

    date = datetime.now().strftime('%Y-%m-%d')

    # 시장 점수 변환 (빈 문자열 또는 None 처리)
    try:
        score = int(market_score) if market_score and market_score != '' else 0
    except (ValueError, TypeError):
        score = 0
        market_score = "0"

    if should_run == 'true':
        # 분석 완료
        if score >= 2:
            emoji = "🟢"
            strategy = "적극 매수 가능"
        elif score >= 0:
            emoji = "🟡"
            strategy = "선별 매수"
        else:
            emoji = "🟠"
            strategy = "신중한 매수"

        message = f"""
🌙 *저녁 전체 분석 완료* ({date})

{emoji} *시장 점수: {market_score}/3*

📊 *분석 결과*
• 분석 종목: {total_stocks}개
• 투자 전략: {strategy}

[📥 전체 결과 보기]({run_url})

💡 *내일 아침 7:50* 시장 재체크 예정
"""
    else:
        # 분석 생략
        message = f"""
🌙 *시장 약세로 분석 생략* ({date})

🔴 *시장 점수: {market_score}/3*

🛑 *권장 조치*
• 매수 보류
• 시장 회복 대기
• 골든크로스 발생 시 자동 재개

💡 *내일 아침 7:50* 시장 체크 예정
"""

    return message


def main():
    parser = argparse.ArgumentParser(description='텔레그램 알림 전송')
    parser.add_argument('--token', required=True, help='텔레그램 봇 토큰')
    parser.add_argument('--chat-id', required=True, help='텔레그램 채팅 ID')
    parser.add_argument('--type', required=True, choices=['morning', 'evening'],
                       help='알림 타입')
    parser.add_argument('--market-score', required=True, help='시장 점수')

    # 아침용 파라미터
    parser.add_argument('--verdict', help='시장 판정')
    parser.add_argument('--golden-cross', default='', help='골든크로스 정보')

    # 저녁용 파라미터
    parser.add_argument('--should-run', help='분석 실행 여부')
    parser.add_argument('--total-stocks', default='0', help='분석 종목 수')
    parser.add_argument('--run-url', help='GitHub Actions 실행 URL')

    args = parser.parse_args()

    # 텔레그램 설정 확인
    if not args.token or args.token == '':
        print("⚠️ 텔레그램 토큰이 설정되지 않았습니다. 알림을 건너뜁니다.")
        sys.exit(0)

    if not args.chat_id or args.chat_id == '':
        print("⚠️ 텔레그램 채팅 ID가 설정되지 않았습니다. 알림을 건너뜁니다.")
        sys.exit(0)

    # 메시지 포맷
    if args.type == 'morning':
        message = format_morning_message(
            args.market_score,
            args.verdict or "알 수 없음",
            args.golden_cross
        )
    else:  # evening
        message = format_evening_message(
            args.market_score,
            args.should_run or 'false',
            args.total_stocks,
            args.run_url or ''
        )

    # 전송
    success = send_telegram_message(args.token, args.chat_id, message)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
