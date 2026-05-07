from pathlib import Path

import pandas as pd
import yfinance as yf


SAMPLE_PRICE_DATA_PATH = Path(__file__).resolve().parent / "sample_data" / "prices.csv"


class PriceDownloadError(RuntimeError):
    """价格数据下载失败。"""


def normalize_price_data(prices: pd.Series | pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """统一价格数据格式，并确认所有标的都有数据。"""
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    normalized = prices.reindex(columns=tickers).dropna(how="all")
    missing_tickers = [
        ticker
        for ticker in tickers
        if ticker not in normalized or normalized[ticker].dropna().empty
    ]
    if normalized.empty or missing_tickers:
        missing_text = ", ".join(missing_tickers) if missing_tickers else "全部标的"
        raise PriceDownloadError(f"价格数据缺失: {missing_text}")

    return normalized


def download_yahoo_price_data(
    tickers: list[str],
    start: str,
    end: str | None = None,
) -> pd.DataFrame:
    """使用 Yahoo Finance 下载 ETF 的复权收盘价。"""
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise PriceDownloadError("Yahoo Finance 返回空数据。")

    close_prices = data["Close"].copy()
    return normalize_price_data(close_prices, tickers)


def load_cached_price_data(
    cache_path: Path,
    tickers: list[str],
    start: str,
    end: str | None = None,
) -> pd.DataFrame:
    """从本地缓存读取价格数据。"""
    if not cache_path.exists():
        raise PriceDownloadError(f"本地缓存不存在: {cache_path}")

    prices = pd.read_csv(cache_path, index_col="Date", parse_dates=True)
    prices = normalize_price_data(prices, tickers)
    prices = prices.loc[prices.index >= pd.Timestamp(start)]
    if end is not None:
        prices = prices.loc[prices.index <= pd.Timestamp(end)]

    return normalize_price_data(prices, tickers)


def load_bundled_sample_price_data(
    tickers: list[str],
    start: str,
    end: str | None = None,
) -> pd.DataFrame:
    """读取仓库内置样例价格数据，保证离线或限流时仍可运行。"""
    return load_cached_price_data(SAMPLE_PRICE_DATA_PATH, tickers, start, end)


def download_price_data(
    tickers: list[str],
    start: str,
    end: str | None = None,
    cache_path: Path | None = None,
) -> pd.DataFrame:
    """下载价格数据：优先 Yahoo，失败后尝试本地缓存和内置样例数据。"""
    errors: list[str] = []

    try:
        prices = download_yahoo_price_data(tickers, start, end)
        print("价格数据来源: Yahoo Finance")
        return prices
    except Exception as error:
        errors.append(f"Yahoo Finance: {error}")

    if cache_path is not None:
        try:
            prices = load_cached_price_data(cache_path, tickers, start, end)
            print(f"价格数据来源: 本地缓存 {cache_path}")
            return prices
        except Exception as error:
            errors.append(f"本地缓存: {error}")

    try:
        prices = load_bundled_sample_price_data(tickers, start, end)
        print(f"价格数据来源: 内置样例数据 {SAMPLE_PRICE_DATA_PATH}")
        return prices
    except Exception as error:
        errors.append(f"内置样例数据: {error}")

    detail = "；".join(errors)
    raise ValueError(f"没有下载到数据，也没有可用的本地数据。失败原因：{detail}")


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
