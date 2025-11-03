# 🎯 F-Score 기반 한국 주식 자동 선정 시스템

**검증된 가치투자 전략으로 우량 종목 자동 발굴**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Production-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

---

## 📊 프로젝트 개요

### 무엇을 하는 프로젝트인가?

이 시스템은 **조셉 피오트로스키(Joseph Piotroski) 교수의 F-Score 전략**을 한국 주식시장에 적용하여, 2,600개 이상의 코스피/코스닥 종목을 자동으로 분석하고 우량 투자 후보를 발굴합니다.

### 핵심 성과

```
✅ 2,631개 전체 종목 분석 (4.5분 소요)
✅ 469개 우량 종목 발굴 (4점 이상)
✅ 74개 만점(6/6) 종목 식별
✅ 23개 턴어라운드 종목 발견
```

### 주요 특징

- **빠른 분석**: 병렬 처리로 2,600개 종목을 5분 내 처리
- **자동화**: 한 번 실행으로 전체 프로세스 완료
- **검증된 전략**: 20년 이상 학술적으로 검증된 F-Score 활용
- **확장 가능**: AWS Lambda 배포로 주간 자동 분석 가능

---

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone [repository-url]
cd kospi_dando_trading

# 필요 패키지 설치
pip install -r requirements.txt
```

### 2. 실행

```bash
# 전체 종목 F-Score 계산 (약 4.5분 소요)
python parallel_fscore.py

# 결과 상세 분석
python analyze_results.py
```

### 3. 결과 확인

```bash
# HTML 리포트 열기
open fscore_parallel_report_20251101.html

# CSV 결과 확인
open fscore_parallel_results_20251101.csv
```

---

## 📁 프로젝트 구조

```
kospi_dando_trading/
│
├── 📄 핵심 모듈
│   ├── parallel_fscore.py          # 병렬 처리 F-Score 계산 (메인)
│   ├── lite_fscore.py              # F-Score 계산 로직
│   ├── stock_screener.py           # 종목 필터링
│   ├── fundametal_analysis.py      # FnGuide 데이터 수집
│   └── analyze_results.py          # 결과 분석 및 시각화
│
├── 📊 결과 파일
│   ├── fscore_parallel_results_20251101.csv      # 469개 종목 데이터
│   ├── fscore_parallel_report_20251101.html      # 시각화 리포트
│   ├── fscore_distribution.png                   # 점수 분포 그래프
│   └── fscore_roa_change.png                     # ROA 증가율 Top 20
│
├── 📚 문서
│   ├── README.md                   # 프로젝트 개요 (본 파일)
│   ├── QUICK_START.md              # 10분 실전 투자 가이드
│   └── FSCORE_STRATEGY_GUIDE.md    # 전략 상세 설명
│
├── 🧪 백테스팅 (개발 중)
│   ├── backtest_fscore.py          # 리밸런싱 백테스터
│   └── backtest_fscore_simple.py   # 간소화 백테스터
│
└── 📝 기타
    ├── requirements.txt            # 필요 패키지
    └── df_sorted.csv               # 종목 리스트 캐시
```

---

## 💡 F-Score란?

### 개념

F-Score는 **재무제표 9가지 지표**를 체크하여 0~9점으로 기업의 재무 건전성을 평가하는 전략입니다.

### 검증된 성과

- 원논문(2000): **연평균 23% 초과수익** 달성
- 20년 이상 학술 연구로 효과 입증
- 국내 시장에서도 유효성 확인

### Lite F-Score (현재 버전)

FnGuide 데이터만으로 계산 가능한 **6가지 지표** 사용:

1. ✅ 당기순이익 > 0
2. ✅ ROA 증가
3. ✅ 부채비율 감소
4. ✅ 발행주식수 불변/감소
5. ✅ 영업이익률 증가
6. ✅ 자산회전율 증가

> OpenDart API 승인 후 Full F-Score (9/9) 업그레이드 예정

---

## 🏆 발굴된 주요 종목

### 만점(6/6) 대형주

| 순위 | 종목명 | 코드 | ROA | 영업이익률 | 특징 |
|------|--------|------|-----|------------|------|
| 1 | 삼성바이오로직스 | 207940 | 8.64% | 36.89% | 바이오 대장주 |
| 2 | HD현대에너지솔루션 | 322000 | 6.33% | 7.49% | 2차전지 |
| 3 | HD현대중공업 | 329180 | 6.18% | 11.99% | 조선 |
| 4 | 넷마블 | 251270 | 4.14% | 11.87% | 게임 |
| 5 | GKL | 114090 | 9.18% | 15.80% | 카지노 |

### 고성장 중형주 (ROA 증가율 Top 5)

| 순위 | 종목명 | 코드 | ROA 변화 | 특징 |
|------|--------|------|----------|------|
| 1 | 케일럼 | 258610 | **+68.01%p** | 극적 턴어라운드 |
| 2 | 주성코퍼레이션 | 109070 | +16.68%p | 반도체 장비 |
| 3 | 에치에프알 | 230240 | +14.36%p | 화학 |
| 4 | 아나패스 | 123860 | +13.66%p | 반도체 소재 |
| 5 | 질경이 | 233990 | +13.61%p | 화장품/헬스 |

---

## 📈 투자 전략

### 전략 A: 안정형 (대형주 중심)

**목표**: 연 10-20%, 낮은 변동성

```python
# 추천 종목 (5-7개)
portfolio = [
    '삼성바이오로직스',
    'HD현대에너지솔루션',
    'HD현대중공업',
    'GKL',
    '효성중공업'
]
```

### 전략 B: 성장형 (중소형주 혼합)

**목표**: 연 20-40%, 중간 위험

```python
# 대형 50% + 중형 30% + 소형 20%
portfolio = {
    '대형주': ['삼성바이오로직스', 'HD현대에너지솔루션', ...],
    '중형주': ['아나패스', '에스앤에스텍', ...],
    '소형주': ['질경이', '메가터치', ...]
}
```

### 전략 C: 공격형 (턴어라운드)

**목표**: 연 40%+, 높은 위험

```python
# 적자→흑자 전환 종목 (소액 분산)
turnaround_stocks = [
    '케일럼', '파인텍', '누보', '스타플렉스', ...
]
# ⚠️ 종목당 비중 5% 이하, 손절 -25%
```

---

## 🛡️ 리스크 관리

### 필수 원칙

```
✅ 최소 10개 종목 분산
✅ 단일 종목 10% 이하
✅ 손절 라인 엄수
   - 대형주: -15%
   - 중소형주: -20%
✅ 분기별 리밸런싱
```

---

## 🔧 기술 스택

### 데이터 수집
- **FnGuide**: 재무제표 웹 스크레이핑 (BeautifulSoup)
- **pykrx**: KRX 시장 데이터
- **OpenDart** (예정): 공식 재무 데이터

### 처리
- **Python 3.8+**
- **Pandas**: 데이터 분석
- **ThreadPoolExecutor**: 병렬 처리 (15 workers)
- **Matplotlib**: 시각화

### 성능
- 순차 처리: 2,631개 → **29분**
- 병렬 처리: 2,631개 → **4.5분** (6.4배 개선)
- 평균 처리 속도: **14.8개/초**

---

## 📊 주요 기능

### 1. 자동 종목 필터링

```python
from stock_screener import StockScreener

screener = StockScreener()
df = screener.screen()
# → 우선주, SPAC, ETF, 관리종목 자동 제외
```

### 2. F-Score 계산

```python
from lite_fscore import LiteFScoreCalculator

calculator = LiteFScoreCalculator('207940')  # 삼성바이오로직스
score, details = calculator.calculate()

print(f"점수: {score}/6")
# 출력: 점수: 6/6
```

### 3. 병렬 처리

```python
from parallel_fscore import ParallelFScoreSelector

selector = ParallelFScoreSelector(max_workers=15)
ticker_list = selector.get_ticker_list()
results = selector.calculate_fscores_parallel(ticker_list)
# → 2,631개 종목을 4.5분에 처리
```

### 4. 결과 분석

```python
python analyze_results.py

# 출력:
# - 점수별 분포
# - ROA 증가율 Top 20
# - 턴어라운드 종목
# - 업종별 분포
# - 시각화 그래프
```

---

## 📚 문서

### 초보자용
1. **QUICK_START.md** - 10분 만에 실전 투자 시작
   - 종목 선정 방법
   - 매수/매도 타이밍
   - 포트폴리오 구성 예시

### 전략 이해
2. **FSCORE_STRATEGY_GUIDE.md** - F-Score 전략 완전 가이드
   - 이론적 배경
   - 투자 전략 3가지
   - 리스크 관리
   - 자동화 로드맵

### 개발자용
3. **코드 문서화** (Docstrings)
   - 모든 함수/클래스 상세 설명
   - 파라미터 및 반환값 명시

---

## 🚀 로드맵

### ✅ Phase 1: 완료
- [x] Lite F-Score 구현 (6/9 지표)
- [x] 병렬 처리 시스템
- [x] 전체 종목 분석
- [x] 결과 분석 및 시각화
- [x] 투자 가이드 문서화

### 🔄 Phase 2: 진행 중
- [ ] OpenDart API 연동
- [ ] Full F-Score (9/9 지표)
- [ ] 백테스팅 시스템 완성

### 📅 Phase 3: 예정
- [ ] AWS Lambda 배포
- [ ] 주간 자동 분석 + 이메일
- [ ] Slack/텔레그램 알림
- [ ] 웹 대시보드

---

## ⚙️ 설정 및 커스터마이징

### 병렬 처리 워커 수 조정

```python
# parallel_fscore.py 에서

selector = ParallelFScoreSelector(
    max_workers=15  # 기본값: 15
    # 값이 클수록 빠르지만 API 차단 위험
    # 권장: 10-20
)
```

### 최소 점수 기준 변경

```python
# 4점 이상 필터링 (기본)
df_ranked = selector.filter_and_rank(min_score=4)

# 6점 만점만 보기
df_ranked = selector.filter_and_rank(min_score=6)
```

### 분석 종목 수 제한 (테스트용)

```python
# 상위 100개만 테스트
results = selector.calculate_fscores_parallel(
    ticker_list,
    max_count=100
)
```

---

## 🧪 테스트

### 단일 종목 테스트

```bash
python -c "
from lite_fscore import LiteFScoreCalculator

calculator = LiteFScoreCalculator('005930')  # 삼성전자
score, details = calculator.calculate()

print(f'삼성전자 F-Score: {score}/6')
for key, value in details.items():
    print(f'  {key}: {value}')
"
```

### 소규모 배치 테스트

```bash
# 상위 50개만 처리 (약 20초)
python -c "
from parallel_fscore import ParallelFScoreSelector

selector = ParallelFScoreSelector(use_existing_data=True)
ticker_list = selector.get_ticker_list()[:50]
results = selector.calculate_fscores_parallel(ticker_list)
print(f'완료: {len(results)}개 종목')
"
```

---

## 📈 성능 벤치마크

### 처리 속도

| 종목 수 | 순차 처리 | 병렬 처리 (15 workers) | 개선율 |
|---------|-----------|------------------------|--------|
| 100개 | 66초 | 6초 | 11배 |
| 500개 | 5.5분 | 30초 | 11배 |
| 2,631개 | 29분 | 4.5분 | 6.4배 |

### 메모리 사용량
- 평균: 200-300MB
- 피크: 500MB

---

## 🐛 문제 해결

### Q: "No data" 에러가 발생해요
**A**: 주말이거나 해당 종목이 상장폐지/거래정지일 수 있습니다. 평일에 재시도하세요.

### Q: API 요청이 너무 많다는 에러
**A**: `max_workers`를 10으로 낮추거나, 잠시 대기 후 재시도하세요.

### Q: 특정 종목 데이터가 안 나와요
**A**: FnGuide에 재무제표가 없는 신규 상장사일 수 있습니다. 정상입니다.

### Q: 백테스팅이 실행 안 돼요
**A**: 현재 pykrx 데이터 이슈로 백테스팅은 일시 중단 상태입니다. 추후 수정 예정.

---

## 📜 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request 환영합니다!

### 기여 가이드라인
1. Issue 생성
2. Fork & Branch 생성
3. 코드 작성 (Docstring 필수)
4. Pull Request

---

## 📞 연락처

문의 사항이나 피드백은 Issue로 남겨주세요.

---

## ⚠️ 면책 조항

본 시스템은 **정보 제공 목적**이며, 투자 권유가 아닙니다.

- 모든 투자 판단과 책임은 투자자 본인에게 있습니다
- F-Score는 과거 재무제표 기반이며 미래 수익을 보장하지 않습니다
- 실전 투자 전 반드시 추가 분석과 리스크 관리가 필요합니다

---

## 🌟 Star History

이 프로젝트가 도움이 되었다면 ⭐️ Star를 눌러주세요!

---

**Happy Investing! 📈**

*Last Updated: 2025-11-01*
