# AGENTS.md

## Cursor Cloud specific instructions

Python CLI tool for ETF monthly 200-day moving average backtesting (QQQ/TLT). See `README.md` for strategy logic and project structure.

### Quick reference

- **Install deps:** `pip install -r requirements.txt`
- **Run:** `python3 main.py` — downloads live data from Yahoo Finance, runs backtest, prints results, and writes CSV/PNG to `outputs/`.
- **Python ≥ 3.10** required (uses `str | None` union syntax).
- **No tests, no linter, no build system** in the current codebase.

### Caveats

- Requires internet access to Yahoo Finance (`query1.finance.yahoo.com`). Will raise `ValueError` if data download fails.
- `matplotlib` uses the non-interactive `Agg` backend by default in headless environments — no display needed.
- The `outputs/` directory is created automatically and old files are wiped on each run.
