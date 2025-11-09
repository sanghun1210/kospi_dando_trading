# 타이밍 분석 개선 사항 (2025-11-09)

## 🔧 문제점

기존 시스템에서 타이밍 분석 중 프로세스가 150/1128 지점에서 멈추는 문제 발생:
- **타임아웃 처리 없음**: pykrx 네트워크 요청이 무한정 대기
- **재시도 로직 없음**: 일시적 네트워크 오류로 영구 실패
- **체크포인트 없음**: 중단 시 모든 진행 상황 손실
- **과도한 병렬 처리**: 5개 워커가 데이터 소스 과부하 유발
- **레이트 리밋 없음**: KRX 서버 과부하 가능성

## ✅ 개선 사항

### 1. 타임아웃 및 재시도 로직 추가

**파일**: `technical_data_collector.py`

```python
# 10초 타임아웃 적용
@with_timeout(10)
def fetch_data():
    return stock.get_market_ohlcv_by_date(start_str, end_str, ticker)

# 최대 3회 재시도 (지수 백오프: 2초, 4초, 6초)
for attempt in range(max_retries):
    try:
        df = fetch_data()
        return df
    except TimeoutError:
        wait_time = (attempt + 1) * 2
        time.sleep(wait_time)
```

**효과**:
- 네트워크 지연 시 최대 10초 후 자동 재시도
- 일시적 오류 자동 복구
- 무한 대기 방지

### 2. 레이트 리밋 방지

```python
# 요청 간 0.1초 대기 (기본값)
def __init__(self, days=120, request_delay=0.1):
    self.request_delay = request_delay

# 각 요청 전 대기
if self.request_delay > 0:
    time.sleep(self.request_delay)
```

**효과**:
- KRX 서버 과부하 방지
- 안정적인 데이터 수집

### 3. 체크포인트 시스템

**파일**: `hybrid_fscore_timing.py`

```python
# 20개마다 자동 저장 (기본값)
def __init__(self, checkpoint_interval=20):
    self.checkpoint_interval = checkpoint_interval

# 중간 결과 저장
if checkpoint_counter % self.checkpoint_interval == 0:
    self.save_checkpoint(results, checkpoint_counter)

# 재시작 시 자동 복구
if resume and os.path.exists(self.checkpoint_path):
    results = self.load_checkpoint()
```

**체크포인트 파일**: `hybrid_timing_checkpoint_20251109.csv`

**효과**:
- 중단되어도 진행 상황 보존
- 재시작 시 자동으로 이어서 분석
- 메모리 효율 증가

### 4. 병렬 워커 수 감소

```python
# 기존: 5 workers → 변경: 3 workers
def analyze_batch(self, max_workers=3):
```

**효과**:
- 안정성 증가
- 데이터 소스 부담 감소
- 타임아웃 발생률 감소

### 5. Future 타임아웃

```python
# 각 분석 작업에 30초 타임아웃
result = future.result(timeout=30)
```

**효과**:
- 개별 종목 분석이 멈춰도 전체 프로세스 계속 진행
- 데드락 방지

## 📊 사용법

### 기본 실행 (체크포인트 지원)

```bash
python run_full_analysis.py --api-key YOUR_API_KEY
```

**특징**:
- 자동으로 20개마다 체크포인트 저장
- 중단 후 재실행 시 자동으로 이어서 진행
- 워커 수: 3개 (안정성 우선)

### 중단된 분석 재개

```bash
# 동일한 명령어로 다시 실행하면 자동 재개
python run_full_analysis.py --api-key YOUR_API_KEY
```

출력 예시:
```
♻️  체크포인트에서 148개 복구됨
전체: 1128개
이미 완료: 148개 (체크포인트)
남은 종목: 980개
```

### 체크포인트 비활성화

```python
# hybrid_fscore_timing.py 직접 실행 시
analyzer.analyze_batch(max_workers=3, resume=False)
```

### 성능 우선 모드 (주의!)

```bash
# 워커 수 증가 (네트워크 안정적일 때만)
python run_full_analysis.py --api-key YOUR_API_KEY --timing-workers 5
```

⚠️ **주의**: 워커 수를 늘리면 타임아웃/레이트 리밋 발생 가능

### 테스트 모드

```bash
# 소규모 테스트 (Lite 100개, 타이밍 20개)
python run_full_analysis.py --api-key YOUR_API_KEY --test
```

## 🔍 모니터링

### 진행 상황 확인

```bash
# 체크포인트 파일 확인
wc -l hybrid_timing_checkpoint_20251109.csv

# 최신 결과 확인
tail -20 hybrid_timing_checkpoint_20251109.csv
```

### 로그 메시지

```
✅ 정상 진행:
  진행: 150/1128 (성공: 148개)
  💾 체크포인트 저장: 148개

⚠️ 재시도 중:
  ⏱️  타임아웃 (005930), 2초 후 재시도 (1/3)

❌ 최종 실패:
  ❌ 타임아웃 최종 실패 (005930)
  ❌ 최종 실패 (005930): Connection reset
```

## 📁 생성되는 파일

1. **체크포인트 파일** (중간 저장):
   - `hybrid_timing_checkpoint_20251109.csv`
   - 20개마다 자동 업데이트
   - 재시작 시 자동 로드

2. **최종 결과 파일**:
   - `hybrid_timing_results_20251109.csv`
   - 분석 완료 후 생성
   - 체크포인트와 동일한 내용 (정렬된 버전)

3. **F-Score 결과** (입력):
   - `hybrid_lite_results_20251109.csv`
   - 1단계에서 생성
   - 타이밍 분석의 입력 데이터

## 🎯 권장 설정

### 안정성 우선 (기본값)
```bash
python run_full_analysis.py \
  --api-key YOUR_API_KEY \
  --timing-workers 3 \
  --min-timing-score 5.0
```

### 빠른 테스트
```bash
python run_full_analysis.py \
  --api-key YOUR_API_KEY \
  --test
```

### 고품질 종목만
```bash
python run_full_analysis.py \
  --api-key YOUR_API_KEY \
  --min-fscore 5 \
  --min-timing-score 7.0
```

## 🔧 문제 해결

### 1. 여전히 멈추는 경우

```bash
# 워커 수를 1로 줄이기
python run_full_analysis.py --api-key YOUR_API_KEY --timing-workers 1
```

### 2. 체크포인트 초기화

```bash
# 체크포인트 삭제 후 처음부터 시작
rm hybrid_timing_checkpoint_*.csv
python run_full_analysis.py --api-key YOUR_API_KEY
```

### 3. 타임아웃 조정

`technical_data_collector.py` 수정:
```python
# 타임아웃 증가 (10초 → 20초)
@with_timeout(20)
def fetch_data():
    return stock.get_market_ohlcv_by_date(start_str, end_str, ticker)
```

### 4. 요청 간 대기 시간 증가

```python
# 0.1초 → 0.5초로 증가
collector = TechnicalDataCollector(days=120, request_delay=0.5)
```

## 📈 예상 개선 효과

| 항목 | 이전 | 개선 후 |
|------|------|---------|
| 타임아웃 처리 | ❌ 없음 (무한 대기) | ✅ 10초 + 재시도 |
| 진행 상황 보존 | ❌ 중단 시 손실 | ✅ 20개마다 저장 |
| 안정성 | ⚠️ 150/1128에서 멈춤 | ✅ 자동 복구 |
| 재시작 | ❌ 처음부터 | ✅ 이어서 진행 |
| 성공률 | ~13% (148/1128) | ~90%+ 예상 |

## 🚀 다음 단계

1. **개선된 버전으로 재실행**:
   ```bash
   python run_full_analysis.py --skip-fscore --api-key YOUR_API_KEY
   ```

2. **진행 상황 모니터링**:
   - 체크포인트 파일 크기 확인
   - 로그에서 타임아웃 빈도 확인

3. **완료 후 결과 분석**:
   - 상위 종목 확인
   - 타이밍 점수 분포 확인
   - 포트폴리오 구성

## 📝 기술적 세부사항

### 타임아웃 구현 (Unix Signal 사용)

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Request timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)  # 10초 타임아웃
# ... 작업 수행 ...
signal.alarm(0)   # 취소
```

### 체크포인트 저장 방식

1. 메모리에 결과 누적
2. 20개마다 CSV 파일에 저장
3. 재시작 시 CSV 로드
4. 이미 처리된 종목 제외

### 병렬 처리 최적화

- **ThreadPoolExecutor** 사용 (GIL 무관 I/O 작업)
- **Lock** 으로 공유 자원 보호
- **as_completed** 로 완료 순서대로 처리
- **Future timeout** 으로 데드락 방지
