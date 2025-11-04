# 📖 Full F-Score 시스템 사용 가이드

## 🎯 3가지 실행 방법

### 1️⃣ Hybrid F-Score (권장) ⭐

**가장 효율적인 방법으로 최고 품질의 결과를 얻습니다.**

```bash
python hybrid_fscore.py
```

**작동 방식:**
- 1단계: Lite F-Score로 전체 2,631개 종목 스캔 (4.5분)
- 2단계: 상위 200개만 Full F-Score 정밀 분석 (7분)
- **총 소요 시간: 약 11.5분**

**결과 파일:**
- `hybrid_lite_results_YYYYMMDD.csv` - 1단계 전체 결과
- `hybrid_full_results_YYYYMMDD.csv` - 2단계 정밀 결과 (7-9점 우량주)
- `full_fscore_report_YYYYMMDD.html` - 시각화 리포트

**추천 대상:**
- 최고 품질의 종목을 찾고 싶은 투자자
- 시간 효율과 정확도를 모두 원하는 경우

---

### 2️⃣ Lite F-Score (빠른 스캔)

**전체 시장을 빠르게 스캔하여 우량 후보를 찾습니다.**

```bash
python parallel_fscore.py
```

**작동 방식:**
- FnGuide 데이터만 사용 (6/9 지표)
- 전체 2,631개 종목 분석
- **소요 시간: 약 4.5분**

**결과 파일:**
- `fscore_parallel_results_YYYYMMDD.csv`
- `fscore_parallel_report_YYYYMMDD.html`

**추천 대상:**
- 빠르게 전체 시장을 둘러보고 싶은 경우
- OpenDart API 없이 사용하고 싶은 경우

---

### 3️⃣ Full F-Score (단일 종목 정밀 분석)

**특정 종목을 상세하게 분석합니다.**

```bash
python full_fscore.py
```

또는 Python 코드:

```python
from full_fscore import FullFScoreCalculator

api_key = "your_opendart_api_key"
calculator = FullFScoreCalculator('005930', api_key)  # 삼성전자
score, details = calculator.calculate('2023')

print(f"점수: {score}/9")
calculator.get_score_breakdown(details)
```

**추천 대상:**
- 관심 종목을 상세히 분석하고 싶은 경우
- 9가지 지표를 모두 확인하고 싶은 경우

---

## 🔧 상세 설정

### 테스트 모드 (빠른 확인용)

**hybrid_fscore.py 수정:**

```python
# 파일 마지막 부분
if __name__ == "__main__":
    main(test_mode=True)  # True로 설정
```

테스트 모드:
- Lite: 상위 100개만
- Full: 상위 30개만
- 소요 시간: 약 1-2분

### 전체 실행 (프로덕션)

```python
if __name__ == "__main__":
    main(test_mode=False)  # False로 설정
```

전체 실행:
- Lite: 전체 2,631개
- Full: 상위 200개 (7점 이상 최종 선정)
- 소요 시간: 약 11.5분

---

## 📊 결과 해석

### CSV 파일 주요 컬럼

| 컬럼명 | 설명 |
|--------|------|
| `code` | 종목 코드 (6자리) |
| `name` | 종목명 |
| `score` | F-Score 총점 (0-9점) |
| `lite_score` | Lite F-Score (0-6점) |
| `additional_score` | OpenDart 추가 점수 (0-3점) |
| `roa_current` | 현재 ROA (%) |
| `operating_margin_current` | 현재 영업이익률 (%) |
| `debt_ratio_current` | 현재 부채비율 (%) |

### 점수별 의미

| 점수 | 평가 | 투자 의미 |
|------|------|-----------|
| **9점** | 완벽 | 매우 우량, 최우선 검토 |
| **8점** | 우수 | 우량주, 포트폴리오 핵심 |
| **7점** | 양호 | 좋은 투자 후보 |
| **6점** | 보통+ | 검토 가능 (Lite 만점) |
| **4-5점** | 보통 | 신중한 검토 필요 |
| **0-3점** | 부진 | 투자 비추천 |

---

## 🛠️ 문제 해결

### Q: "No data" 에러 발생

**A:**
- 주말이거나 FnGuide에 데이터가 없는 종목
- 평일에 재시도하거나, 해당 종목 제외

### Q: OpenDart API 에러

**A:**
```bash
# API 키 확인
python -c "
from opendart_client import OpenDartClient
client = OpenDartClient('your_api_key')
print('API 키 정상')
"
```

### Q: 실행 속도가 느림

**A:**
```python
# parallel_fscore_full.py에서 워커 수 조정
selector = ParallelFullFScoreSelector(
    opendart_api_key=api_key,
    max_workers=5  # 10 → 5로 줄임 (안정적)
)
```

### Q: 메모리 부족

**A:**
- 테스트 모드로 먼저 실행
- 또는 max_count 파라미터로 처리 개수 제한

---

## 💡 추천 워크플로우

### 주간 루틴 (매주 금요일)

```bash
# 1. 전체 시장 스캔
python hybrid_fscore.py

# 2. 결과 확인
open hybrid_full_results_YYYYMMDD.csv

# 3. 7점 이상 종목 리스트 작성
# 4. 각 종목 차트, 공시, 뉴스 확인
# 5. 포트폴리오 업데이트
```

### 분기별 루틴 (결산 발표 후)

```bash
# 1. 최신 재무제표 반영되면 재실행
python hybrid_fscore.py

# 2. 기존 보유 종목 재평가
python -c "
from full_fscore import FullFScoreCalculator

api_key = 'your_key'
my_stocks = ['005930', '207940', '251270']  # 보유 종목

for code in my_stocks:
    calc = FullFScoreCalculator(code, api_key)
    score, _ = calc.calculate()
    print(f'{code}: {score}/9')
"

# 3. 점수 하락 종목은 매도 검토
# 4. 신규 고득점 종목 발굴
```

---

## 📈 성능 벤치마크

| 작업 | 종목 수 | 소요 시간 | 처리 속도 |
|------|---------|-----------|-----------|
| Lite F-Score | 2,631개 | 4.5분 | 14.8개/초 |
| Full F-Score | 200개 | 7분 | 0.5개/초 |
| Hybrid 전체 | 2,631 → 200 | 11.5분 | - |

**시스템 사양:** Apple M1, 16GB RAM

---

## 🔐 보안 주의사항

### API 키 관리

```bash
# .env 파일 사용 (권장)
echo "OPENDART_API_KEY=your_key" > .env
echo ".env" >> .gitignore

# Python에서 로드
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENDART_API_KEY')
```

**절대 하지 말 것:**
- ❌ API 키를 코드에 하드코딩
- ❌ GitHub에 .env 파일 커밋
- ❌ API 키를 공개 저장소에 노출

---

## ✅ 완료!

이제 Full F-Score 시스템을 사용할 준비가 되었습니다!

**다음 단계:**
1. `python hybrid_fscore.py` 실행
2. 결과 CSV 확인
3. 고득점 종목 분석
4. 투자 포트폴리오 구성

**추가 문서:**
- `README.md` - 프로젝트 전체 개요
- `QUICK_START.md` - 10분 투자 가이드
- `FSCORE_STRATEGY_GUIDE.md` - 전략 상세 설명

**문의 및 피드백:**
- GitHub Issues로 문의해주세요!

Happy Investing! 📈
