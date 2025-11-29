# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean stock screening and analysis system that combines:
1. **F-Score Analysis** (fundamental): Piotroski's 9-point financial health score
2. **Technical Analysis** (timing): Chart-based buy/sell signals using technical indicators

The system analyzes 2,600+ KOSPI/KOSDAQ stocks in ~11 minutes to identify high-quality investment candidates with optimal entry timing.

## Architecture

### Three-Layer Analysis Pipeline

**Layer 1: Lite F-Score (6/9 indicators)**
- Source: FnGuide web scraping
- Processes: All 2,631 stocks in ~4.5 minutes
- Parallel processing: 6 workers (ThreadPoolExecutor)
- Output: `fscore_parallel_results_YYYYMMDD.csv`

**Layer 2: Full F-Score (9/9 indicators)**
- Source: FnGuide + OpenDart API
- Processes: Top 200 stocks from Layer 1 in ~7 minutes
- Adds 3 cash flow indicators from official financial statements
- Output: `hybrid_full_results_YYYYMMDD.csv`

**Layer 3: Technical Timing Analysis**
- Source: pykrx market data
- Analyzes: Chart patterns, indicators (MA, RSI, MACD, Bollinger Bands)
- Checkpoint system: Saves progress every 20 stocks
- Output: `hybrid_timing_results_YYYYMMDD.csv`

### Key Data Flow

```
pykrx (stock list) → StockScreener → [2,631 tickers]
    ↓
FnGuide scraping → LiteFScoreCalculator → ParallelFScoreSelector
    ↓
[Top 200 by Lite F-Score]
    ↓
OpenDart API → FullFScoreCalculator → ParallelFullFScoreSelector
    ↓
[7-9 point stocks]
    ↓
pykrx (OHLCV) → TechnicalDataCollector → TimingSignals
    ↓
[Final ranked list with timing scores]
```

## Common Commands

### Running Analysis

```bash
# Full pipeline: F-Score + Timing (recommended)
python run_full_analysis.py --api-key YOUR_OPENDART_API_KEY

# Skip F-Score if already done today (resume timing analysis)
python run_full_analysis.py --skip-fscore --api-key YOUR_API_KEY

# F-Score only (Hybrid: Lite all → Full top 200)
python hybrid_fscore.py

# Lite F-Score only (fast scan, 6/9 indicators)
python parallel_fscore.py

# Technical timing analysis only
python hybrid_fscore_timing.py --fscore-file hybrid_lite_results_20251109.csv
```

### Testing

```bash
# Run tests
pytest

# Run specific test file
pytest tests/test_lite_fscore.py

# Run with coverage
pytest --cov=. --cov-report=html

# Test single stock F-Score
python -c "from lite_fscore import LiteFScoreCalculator; calc = LiteFScoreCalculator('005930'); print(calc.calculate())"
```

### Debugging

```bash
# Debug OpenDart API connection
python debug_opendart.py

# Test with small sample (100 stocks for Lite, 30 for timing)
python run_full_analysis.py --api-key YOUR_KEY --test

# Check checkpoint recovery
ls -lh hybrid_timing_checkpoint_*.csv
```

## Module Architecture

### Core Calculators

**`lite_fscore.py` - LiteFScoreCalculator**
- Calculates 6/9 F-Score indicators using FnGuide data
- Checks: net income, ROA growth, debt ratio, share count, operating margin, asset turnover
- Dependencies: `fundametal_analysis.py` for web scraping

**`full_fscore.py` - FullFScoreCalculator**
- Adds 3 cash flow indicators: operating CF > 0, OCF > net income, current ratio growth
- Depends on: `lite_fscore.py` + `opendart_client.py`
- Returns 0-9 point score

**`timing_signals.py` - TimingSignals**
- Detects chart patterns: golden cross, RSI zones, MACD crossover, Bollinger bounce
- Scoring: 0-10 points based on buy signal strength
- Input: DataFrame with technical indicators (SMA, RSI, MACD, BBands)

### Data Collection

**`fundametal_analysis.py` - FundamentalAnalysis**
- Web scraping from FnGuide (http://comp.fnguide.com)
- Extracts: income statement, balance sheet, share count, ratios
- Fallback to OpenDart API if FnGuide data missing
- Uses BeautifulSoup + pandas.read_html

**`opendart_client.py` - OpenDartClient**
- Official Korean financial data API client
- Caches corp_code mapping (stock code → company ID)
- Methods: `get_cash_flow_statement()`, `get_financial_statement()`
- Rate limiting: Built-in delays to avoid API throttling

**`technical_data_collector.py` - TechnicalDataCollector**
- Fetches OHLCV data from pykrx
- Calculates: SMA (5/20/60/120), EMA, RSI, MACD, Bollinger Bands
- Timeout handling: 10 seconds with 3 retries
- Request delay: 0.1s between calls (configurable)

### Parallel Processing

**`parallel_fscore.py` - ParallelFScoreSelector**
- ThreadPoolExecutor for concurrent FnGuide scraping
- Default: 6 workers (adjustable via `max_workers`)
- Thread-safe result collection with Lock
- Progress tracking with success/fail counts

**`parallel_fscore_full.py` - ParallelFullFScoreSelector**
- Same pattern but calls FullFScoreCalculator
- Shares OpenDartClient instance across threads (cache reuse)
- Default: 5 workers (slower due to API calls)

**`hybrid_fscore_timing.py` - HybridFScoreTiming**
- Checkpoint system: Auto-saves every 20 stocks
- Resume capability: Loads checkpoint on restart
- Future timeout: 30s per stock to prevent deadlocks
- Default: 3 workers (conservative for stability)

### Utilities

**`stock_screener.py` - StockScreener**
- Filters out: preferred stocks (종목명 includes "우"), SPACs, ETFs, delisted
- Sources ticker list from pykrx
- Saves to `df_sorted.csv` for caching

**`sector_utils.py`**
- Sector classification and scoring adjustments
- Default sector mapping for unknown stocks
- Used in hybrid analysis for sector-based weighting

**`data_handler.py` - StockDataHandler**
- pykrx wrapper for OHLCV data
- Resampling: daily → weekly/monthly
- Column renaming to English (시가 → open_price, etc.)

## Critical Implementation Details

### OpenDart API Key Management

**NEVER** hardcode API keys. Use environment variables:

```bash
# .env file (already in .gitignore)
OPENDART_API_KEY=your_key_here

# Load in code
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENDART_API_KEY')
```

### Checkpoint System (Timing Analysis)

Located in `hybrid_fscore_timing.py`:

```python
# Auto-saves every 20 stocks
checkpoint_interval = 20

# File: hybrid_timing_checkpoint_YYYYMMDD.csv
# Format: Same as final results, updated incrementally

# Resume logic
if resume and os.path.exists(checkpoint_path):
    existing_df = pd.read_csv(checkpoint_path)
    completed_codes = set(existing_df['code'])
    # Skip already-processed stocks
```

**Important**: Always check for existing checkpoints before running timing analysis. The system will automatically resume from the last checkpoint.

### Timeout & Retry Pattern

Used in `technical_data_collector.py`:

```python
# Timeout decorator (Unix signals)
@with_timeout(10)
def fetch_data():
    return stock.get_market_ohlcv_by_date(...)

# Retry loop with exponential backoff
for attempt in range(3):
    try:
        df = fetch_data()
        break
    except TimeoutError:
        wait = (attempt + 1) * 2  # 2s, 4s, 6s
        time.sleep(wait)
```

### Web Scraping Robustness

FnGuide URLs in `fundametal_analysis.py`:

```python
# Primary source
url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A{ticker}"

# Fallback to OpenDart if:
# - HTTP error (timeout, 404, etc.)
# - Empty data returned
# - Parsing fails
```

**Rate limiting**: Built into collectors via `request_delay` parameter. Default 0.1s prevents server blocking.

## F-Score Calculation Details

### Lite F-Score (6/9)

1. Net income > 0
2. ROA increasing (current vs previous year)
3. Debt ratio decreasing
4. Share count not increasing (buybacks good, dilution bad)
5. Operating margin increasing
6. Asset turnover increasing

### Full F-Score Additional (3/9)

7. Operating cash flow > 0
8. Operating cash flow > Net income (accrual quality)
9. Current ratio increasing (liquidity)

**Data sources**:
- Items 1-6: FnGuide web scraping
- Items 7-9: OpenDart API (official financial statements)

### Timing Score (0-10)

- Golden cross (20d > 60d MA): +2 points
- Short-term trend (5d > 20d MA): +1 point
- RSI 30-70 zone: +1 point
- RSI > 50 breakout: +1 point
- MACD > Signal: +2 points
- Bollinger lower band bounce: +1 point
- Volume surge (2x average): +1 point
- Resistance breakout: +1 point

**Final ranking**: `combined_score = fscore * 10 + timing_score * 5`

## File Organization

### Input Files
- `df_sorted.csv`: Cached ticker list from StockScreener
- `.env`: OpenDart API key (git-ignored)

### Output Files (auto-generated with YYYYMMDD suffix)
- `fscore_parallel_results_*.csv`: Lite F-Score results (all stocks)
- `hybrid_lite_results_*.csv`: Lite F-Score from hybrid run
- `hybrid_full_results_*.csv`: Full F-Score (top 200)
- `hybrid_timing_results_*.csv`: Final results with timing scores
- `hybrid_timing_checkpoint_*.csv`: Progress checkpoint (timing layer)
- `*_report_*.html`: Visualization reports (matplotlib charts)

### Documentation
- `README.md`: User-facing overview (Korean)
- `USAGE.md`: Detailed usage guide
- `QUICK_START.md`: 10-minute investment guide
- `FSCORE_STRATEGY_GUIDE.md`: Investment strategy details
- `TECHNICAL_ANALYSIS_PLAN.md`: Technical indicator implementation plan
- `TIMING_ANALYSIS_IMPROVEMENTS.md`: Reliability improvements (timeouts, checkpoints)

### Algorithm Library
- `algorithms/`: Technical indicator implementations (20+ indicators)
- Each algorithm is self-contained: `sma.py`, `rsi.py`, `macd.py`, etc.
- Not all algorithms are actively used (library for future expansion)

## Performance Tuning

### Worker Count Guidelines

```python
# Lite F-Score (web scraping)
ParallelFScoreSelector(max_workers=6)  # Default, stable
# Increase to 10-15 if network is stable
# Decrease to 3-5 if timeouts occur

# Full F-Score (API calls)
ParallelFullFScoreSelector(max_workers=5)  # Default
# OpenDart has stricter rate limits

# Timing Analysis (pykrx)
HybridFScoreTiming(max_workers=3)  # Conservative
# max_workers=1 if persistent timeout issues
# max_workers=5 only if network is very stable
```

### Request Delays

```python
# technical_data_collector.py
TechnicalDataCollector(request_delay=0.1)  # Default
# Increase to 0.5 if rate-limited by KRX

# opendart_client.py
# Built-in delays between API calls
# No user configuration needed
```

### Memory Management

Checkpoint system reduces memory footprint:
- Before: All results in memory until completion
- After: Flush to disk every 20 stocks
- Enables analysis of 2,000+ stocks without OOM

## Testing Strategy

### Test Files
- `tests/test_lite_fscore.py`: Mock FnGuide responses
- `tests/test_full_fscore.py`: Mock OpenDart API
- `tests/test_opendart_client.py`: API client unit tests
- `tests/test_stock_screener.py`: Ticker filtering logic

### Running Tests
- Uses pytest with pytest-mock for external dependencies
- Coverage target: Core calculators and data collectors
- Does NOT test live API calls (uses fixtures)

## Common Issues & Solutions

### "No data" errors during F-Score calculation
- Cause: Stock has no financial data on FnGuide (recent IPO, delisted, etc.)
- Behavior: Calculator returns `(None, None)`, stock is skipped
- Normal: ~5-10% of stocks have missing data

### Timing analysis stops at 150/1128
- Cause: Network timeout without retry logic
- Solution: Implemented in TIMING_ANALYSIS_IMPROVEMENTS.md
- Use: Checkpoint system auto-resumes from last save

### API rate limiting (OpenDart)
- Symptom: HTTP 429 errors or empty responses
- Solution: Reduce `max_workers` in parallel_fscore_full.py
- Built-in: OpenDartClient has request delays

### FnGuide blocking (too many requests)
- Symptom: HTTP errors, empty DataFrames
- Solution: Reduce `max_workers` in parallel_fscore.py
- Add delays: `time.sleep(0.2)` in tight loops

## Environment Setup

```bash
# Python 3.8+ required
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# OpenDart API key setup
echo "OPENDART_API_KEY=your_key" > .env

# Verify installation
python -c "import pandas, pykrx, bs4; print('OK')"
```

## Development Workflow

### Adding New Technical Indicators

1. Create module in `algorithms/your_indicator.py`
2. Add calculation in `technical_data_collector.py`
3. Add signal detection in `timing_signals.py`
4. Update scoring in `TimingSignals.calculate_timing_score()`

### Modifying F-Score Weights

Edit scoring in:
- `lite_fscore.py`: Individual indicator weights
- `full_fscore.py`: Additional indicator weights
- `hybrid_fscore_timing.py`: Combined scoring formula

### Changing Checkpoint Interval

```python
# hybrid_fscore_timing.py
analyzer = HybridFScoreTiming(
    checkpoint_interval=20  # Change to 10, 50, etc.
)
```

## Data Sources & APIs

- **pykrx**: KRX official data (free, no key required)
- **FnGuide**: Web scraping (comp.fnguide.com)
- **OpenDart**: Korean SEC EDGAR (requires free API key from https://opendart.fss.or.kr/)

All data collection respects rate limits and includes error handling for network failures.
