# AGENTS.md

## Cursor Cloud specific instructions

Python CLI tool for ETF monthly 200-day moving average backtesting (QQQ/TLT). See `README.md` for strategy logic and project structure.

### Quick reference

- **Install deps:** `pip install -r requirements.txt`
- **Run:** `python3 main.py` — downloads live data, runs backtest, prints results, and writes CSV/PNG/TXT to `outputs/`.
- **Python ≥ 3.10** required (uses `str | None` union syntax).
- **No tests, no linter, no build system** in the current codebase.

### Caveats

- Data download tries Yahoo Finance first, then `outputs/prices.csv` as a local cache, then bundled `sample_data/prices.csv`.
- `matplotlib` uses the non-interactive `Agg` backend by default in headless environments — no display needed.
- The `outputs/` directory is created automatically and old files are wiped on each run.
