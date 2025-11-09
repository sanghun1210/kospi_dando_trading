# Repository Guidelines

## Project Structure & Module Organization
Source code lives at the repo root; entry points such as `hybrid_fscore.py`, `parallel_fscore.py`, `full_fscore.py`, and `lite_fscore.py` orchestrate the scoring workflows. Support modules (`opendart_client.py`, `stock_screener.py`, `fundametal_analysis.py`, `data_handler.py`) handle API calls and transforms, while experimental logic sits under `algorithms/`. Backtesting utilities are in `backtest_fscore.py` and `backtest_fscore_simple.py`. Generated analytics (`*_results_YYYYMMDD.csv`, `*_report_YYYYMMDD.html`, logs, plots) are reference-only and should stay out of diffs unless intentionally regenerated. Documentation lives in `README.md`, `QUICK_START.md`, `USAGE.md`, and `FSCORE_STRATEGY_GUIDE.md`.

## Build, Test, and Development Commands
- `pip install -r requirements.txt`: install pinned dependencies (Python 3.8+).
- `python hybrid_fscore.py`: run the recommended two-phase pipeline (Lite sweep plus Full refinement). Use `main(test_mode=True)` for a quick smoke run.
- `python parallel_fscore.py`: execute the Lite‑only parallel scan when you need 4–5 minute feedback.
- `python full_fscore.py`: compute a 9/9 score for targeted tickers; accepts CLI args or in-code calls.
- `python backtest_fscore.py`: replay recent picks against historical windows; keep result CSVs out of commits unless the scenario adds lasting value.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, `snake_case` for functions/variables, and `CapWords` for classes (e.g., `FullFScoreCalculator`). Keep modules cohesive—data collectors read external APIs, calculators stay pure, and parallel routines isolate multiprocessing concerns. Use type hints where helpful and prefer f-strings for logging. Run `ruff` or `flake8` locally if available, but favor clarity over strict lint counts.

## Testing Guidelines
No formal test harness exists, so lean on deterministic script outputs. Run the Hybrid flow with `test_mode=True` after code changes to validate data loading, then execute the full pipeline and compare score distributions (`fscore_distribution.png`) for regressions. Backtest scripts double as regression checks—record the command and seed in PR notes. When touching API clients, mock responses via cached rows in `df_sorted.csv` to avoid rate limits.

## Commit & Pull Request Guidelines
Adopt concise, descriptive commits; the history mixes Korean phrases and Conventional Commits (`feat: Hybrid F-Score...`), so standardize on the latter (`feat:`, `fix:`, `chore:`). Each PR should summarize the scenario, list impacted scripts, attach before/after result snippets (score counts or top tickers), and reference any related issue or research note. Screenshots or CSV excerpts belong in the discussion, not the diff.

## Security & Configuration Tips
Store secrets such as `OPENDART_API_KEY` in `.env` (never commit). When sharing notebooks or logs, redact keys and account-specific tickers. Review `requirement.txt` additions for supply-chain risk and pin new packages before merging. EOF
