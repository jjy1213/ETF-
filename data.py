from pathlib import Path

import pandas as pd
import yfinance as yf


def download_price_data(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """使用 yfinance 下载 ETF 的复权收盘价。"""
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise ValueError("没有下载到数据，请检查网络连接、代码或日期范围。")

    close_prices = data["Close"].copy()

    # 当只下载一个标的时，yfinance 可能返回 Series，这里统一成 DataFrame。
    if isinstance(close_prices, pd.Series):
        close_prices = close_prices.to_frame(name=tickers[0])

    return close_prices.dropna(how="all")


def save_outputs(
    output_dir: Path,
    prices: pd.DataFrame,
    moving_average: pd.DataFrame,
    rebalance_signals: pd.Series,
    strategy_result: pd.DataFrame,
    annual_returns: pd.DataFrame,
    performance_summary: pd.Series,
) -> None:
    """保存研究结果，方便后续检查和复盘。"""
    output_dir.mkdir(exist_ok=True)

    # outputs 是运行产物目录，先清掉旧产物，避免上次运行的文件造成误解。
    for old_file in output_dir.glob("*"):
        if old_file.is_file():
            old_file.unlink()

    prices.to_csv(output_dir / "prices.csv", index_label="Date")
    moving_average.to_csv(output_dir / "moving_average.csv", index_label="Date")
    rebalance_signals.to_csv(output_dir / "rebalance_signals.csv", index_label="Date")
    strategy_result.to_csv(output_dir / "strategy_result.csv", index_label="Date")
    strategy_result[["rebalance_signal", "position"]].to_csv(
        output_dir / "signals.csv",
        index_label="Date",
    )
    annual_returns.to_csv(output_dir / "annual_returns.csv")
    performance_summary.to_csv(output_dir / "performance_summary.csv")
