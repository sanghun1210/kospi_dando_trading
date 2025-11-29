# 🚀 GitHub Actions 자동화 설정 가이드

완전 무료로 주식 분석을 자동화합니다!

## 📋 목차

1. [개요](#개요)
2. [설정 방법](#설정-방법)
3. [텔레그램 연동 (선택)](#텔레그램-연동)
4. [사용 방법](#사용-방법)
5. [문제 해결](#문제-해결)

---

## 개요

### ⏰ 실행 스케줄

**아침 시장 체크** (평일 오전 7:50)
- 시장 필터만 빠르게 체크 (2분)
- "오늘 매수 OK/대기" 판단
- 텔레그램 알림

**저녁 전체 분석** (평일 오후 6:00)
- F-Score + 타이밍 전체 분석 (15분)
- 상위 종목 선정
- GitHub Issues에 자동 등록
- 텔레그램으로 요약 전송

### 💰 비용

**완전 무료!**
- GitHub Actions: 월 2,000분 무료 (450분만 사용)
- 결과 저장: GitHub Artifacts (90일) + Issues (영구)

---

## 설정 방법

### 1단계: OpenDart API 키 발급

```bash
1. https://opendart.fss.or.kr/ 접속
2. 회원가입 및 로그인
3. [인증키 신청/관리] 메뉴
4. API 키 발급 (무료)
```

### 2단계: GitHub Secrets 설정

```bash
1. GitHub Repository 페이지 이동
2. Settings → Secrets and variables → Actions
3. "New repository secret" 클릭
4. 아래 시크릿 추가:
```

**필수:**
```
Name: OPENDART_API_KEY
Secret: (발급받은 API 키)
```

**선택 (텔레그램 알림):**
```
Name: TELEGRAM_BOT_TOKEN
Secret: (텔레그램 봇 토큰)

Name: TELEGRAM_CHAT_ID
Secret: (본인의 채팅 ID)
```

### 3단계: Workflow 파일 Push

```bash
# 로컬에서
cd kospi_dando_trading
git add .github/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

### 4단계: 확인

```bash
1. GitHub Repository → Actions 탭
2. 두 개의 workflow 확인:
   - 🌅 Morning Market Check
   - 🌙 Evening Full Analysis
3. "Enable workflows" 클릭 (필요시)
```

---

## 텔레그램 연동 (선택)

### 1. 텔레그램 봇 생성

```
1. 텔레그램에서 @BotFather 검색
2. /newbot 입력
3. 봇 이름 입력 (예: MyStockBot)
4. 봇 사용자명 입력 (예: my_stock_analysis_bot)
5. 토큰 받기: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Chat ID 얻기

```bash
# 1. 봇에게 아무 메시지 보내기 (예: /start)

# 2. 브라우저에서 확인:
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates

# 3. 응답에서 chat.id 찾기:
{
  "message": {
    "chat": {
      "id": 123456789,  ← 이것이 Chat ID
      ...
```

### 3. GitHub Secrets에 추가

```
TELEGRAM_BOT_TOKEN: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID: 123456789
```

---

## 사용 방법

### 자동 실행 (기본)

아무것도 안 해도 됩니다!
- 평일 오전 7:50 - 자동 시장 체크
- 평일 오후 6:00 - 자동 전체 분석

### 수동 실행

```bash
1. GitHub Repository → Actions 탭
2. 원하는 workflow 선택
3. "Run workflow" 버튼 클릭
4. (저녁 분석만) "시장 약세여도 강제 실행" 선택 가능
5. "Run workflow" 확인
```

### 결과 확인

#### A. GitHub Actions (웹)

```
1. Actions 탭 → 최신 실행 클릭
2. Summary 탭에서 요약 확인
3. Artifacts 섹션에서 CSV 다운로드
```

#### B. GitHub Issues (웹/모바일)

```
1. Issues 탭
2. "stock-analysis" 라벨 필터
3. 최신 이슈 열기
4. 상위 10개 종목 + 시장 분석 확인
```

#### C. 텔레그램 (모바일)

```
아침 7:50 - 시장 체크 결과 푸시 알림
저녁 6:00 - 분석 완료 알림 + 요약
```

---

## 실제 사용 시나리오

### 📱 평일 루틴

**아침 (07:50)**
```
[텔레그램 알림]
🌅 아침 시장 체크 (2024-12-02)

🟢 시장 점수: +2/3
판정: 🟢 매수 적극 추천

💰 오늘 매수 전략
✅ 적극 매수 가능
→ 어제 저녁 분석 상위 종목 매수
```

→ **행동**: 9시 장 시작과 동시에 매수

**저녁 (18:00)**
```
[텔레그램 알림]
🌙 저녁 전체 분석 완료 (2024-12-02)

🟢 시장 점수: +2/3
분석 종목: 1,128개

[📥 전체 결과 보기]
```

→ **행동**: GitHub Issues에서 상위 10개 확인, 내일 매수 계획

### 🛑 시장 약세일 때

**아침 (07:50)**
```
🌅 아침 시장 체크

🔴 시장 점수: -2/3
판정: 🔴 매수 대기 권장

💰 오늘 매수 전략
🛑 매수 대기 권장
→ 현금 보유 또는 관망
```

**저녁 (18:00)**
```
🌙 시장 약세로 분석 생략

🔴 시장 점수: -2/3

🛑 권장 조치
• 매수 보류
• 시장 회복 대기
```

→ **행동**: 매수하지 않고 대기

---

## GitHub Issues 예시

```markdown
## 📊 주식 분석 - 2024-12-02

### 🌍 시장 상황
- **시장 점수**: +2/3
- **시장 상태**: 🟢 적극 매수 가능
- **분석 종목 수**: 1,128개

### 🏆 상위 10개 추천 종목

| 순위 | 종목명 | 코드 | F-Score | 타이밍 | 통합점수 |
|------|--------|------|---------|--------|----------|
| 1 | 삼성바이오로직스 | 207940 | 6 | 8.5 | 102.5 |
| 2 | HD현대에너지솔루션 | 322000 | 6 | 8.2 | 101.0 |
...

### 📥 전체 결과 다운로드
[Artifacts에서 다운로드](링크)

### 💡 투자 전략
✅ **적극 매수 가능**
- 상위 종목 중심으로 포트폴리오 구성
- 분산 투자 권장 (10~20개)
```

---

## 문제 해결

### Q: Workflow가 실행되지 않아요

**A:** 다음을 확인하세요:
1. Repository → Settings → Actions → General
2. "Allow all actions" 선택되어 있는지 확인
3. "Workflow permissions" → "Read and write" 선택

### Q: API 키 오류가 나요

**A:** GitHub Secrets 확인:
1. Settings → Secrets → OPENDART_API_KEY
2. 값이 올바른지 확인
3. 앞뒤 공백 없는지 확인

### Q: 텔레그램 알림이 안 와요

**A:**
1. 봇에게 먼저 메시지를 보냈는지 확인 (/start)
2. Chat ID가 숫자만 있는지 확인 (따옴표 없음)
3. 워크플로우 로그에서 에러 확인

### Q: 시간이 안 맞아요

**A:** GitHub Actions는 UTC 시간 사용:
- KST 오전 7:50 = UTC 전날 22:50
- KST 오후 6:00 = UTC 오전 9:00

### Q: 비용이 청구될까요?

**A:** 아니요! 완전 무료입니다.
- GitHub Actions: 월 2,000분 무료
- 이 프로젝트: 월 450분만 사용
- 추가 비용 전혀 없음

### Q: Private 레포지토리에서도 되나요?

**A:** 네! 오히려 권장합니다.
- API 키 보안 강화
- 분석 결과 비공개

---

## 📊 예상 사용량

```
일일 사용:
- 아침 체크: 2분
- 저녁 분석: 15분
- 합계: 17분/일

월간 사용:
- 평일 20일 × 17분 = 340분
- 무료 한도: 2,000분
- 여유분: 1,660분
```

**결론: 완전 무료로 사용 가능!**

---

## 🎯 다음 단계

1. ✅ API 키 발급
2. ✅ GitHub Secrets 설정
3. ✅ Workflow 파일 Push
4. ⏳ 내일 아침 7:50 첫 실행 대기
5. 📱 (선택) 텔레그램 연동

**이제 완전 자동화 완료!** 🎉

---

## 📞 지원

문제가 있으면 GitHub Issues에 등록해주세요.

**Happy Automated Trading!** 📈
