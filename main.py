from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


# 策略参数：保持集中，方便初学者修改
TICKERS = ["QQQ", "TLT"]
START_DATE = "2010-01-01"
END_DATE = None  # None 表示下载到最近一个交易日
LOOKBACK_DAYS = 60
INITIAL_CAPITAL = 1.0
OUTPUT_DIR = Path("outputs")


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

    close_prices = close_prices.dropna(how="all")
    return close_prices


def calculate_momentum(prices: pd.DataFrame, lookback_days: int) -> pd.DataFrame:
    """计算 N 日动量：今天价格 / N 日前价格 - 1。"""
    return prices.pct_change(periods=lookback_days)


def generate_signals(momentum: pd.DataFrame) -> pd.Series:
    """
    生成每日持仓信号。

    规则：
    1. 比较 QQQ 和 TLT 的 60 日动量，选择动量更强的 ETF。
    2. 如果两个 ETF 的动量都小于等于 0，则空仓，记为 CASH。
    """
    best_asset = momentum.idxmax(axis=1)
    best_momentum = momentum.max(axis=1)

    signals = best_asset.where(best_momentum > 0, "CASH")
    signals.name = "signal"
    return signals.dropna()


def calculate_strategy_equity(
    prices: pd.DataFrame,
    signals: pd.Series,
    initial_capital: float,
) -> pd.DataFrame:
    """根据持仓信号计算策略每日收益和资金曲线。"""
    daily_returns = prices.pct_change().fillna(0)

    # 今天收盘得到的信号，下一交易日才开始持有，避免使用未来数据。
    positions = signals.shift(1).reindex(daily_returns.index).fillna("CASH")

    strategy_returns = pd.Series(0.0, index=daily_returns.index, name="strategy_return")
    for ticker in prices.columns:
        strategy_returns.loc[positions == ticker] = daily_returns.loc[positions == ticker, ticker]

    equity_curve = (1 + strategy_returns).cumprod() * initial_capital
    equity_curve.name = "strategy_equity"

    return pd.DataFrame(
        {
            "position": positions,
            "strategy_return": strategy_returns,
            "strategy_equity": equity_curve,
        }
    )


def plot_equity_curve(equity: pd.Series, output_path: Path) -> None:
    """绘制并保存策略资金曲线。"""
    plt.figure(figsize=(12, 6))
    plt.plot(equity.index, equity.values, label="Dual Momentum Strategy", linewidth=2)
    plt.title("QQQ vs TLT Dual Momentum Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def save_outputs(
    prices: pd.DataFrame,
    momentum: pd.DataFrame,
    signals: pd.Series,
    strategy_result: pd.DataFrame,
) -> None:
    """保存研究结果，方便后续检查和复盘。"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    prices.to_csv(OUTPUT_DIR / "prices.csv")
    momentum.to_csv(OUTPUT_DIR / "momentum.csv")
    signals.to_csv(OUTPUT_DIR / "signals.csv")
    strategy_result.to_csv(OUTPUT_DIR / "strategy_result.csv")
    plot_equity_curve(strategy_result["strategy_equity"], OUTPUT_DIR / "equity_curve.png")


def print_summary(strategy_result: pd.DataFrame) -> None:
    """在终端打印简要结果。"""
    final_equity = strategy_result["strategy_equity"].iloc[-1]
    total_return = final_equity / INITIAL_CAPITAL - 1
    latest_position = strategy_result["position"].iloc[-1]

    print("Dual Momentum 回测完成")
    print(f"最新持仓信号: {latest_position}")
    print(f"最终资金曲线值: {final_equity:.4f}")
    print(f"累计收益率: {total_return:.2%}")
    print(f"结果文件已保存到: {OUTPUT_DIR.resolve()}")


def main() -> None:
    """主流程：下载数据 -> 计算动量 -> 生成信号 -> 计算资金曲线 -> 保存结果。"""
    prices = download_price_data(TICKERS, START_DATE, END_DATE)
    momentum = calculate_momentum(prices, LOOKBACK_DAYS)
    signals = generate_signals(momentum)
    strategy_result = calculate_strategy_equity(prices, signals, INITIAL_CAPITAL)

    save_outputs(prices, momentum, signals, strategy_result)
    print_summary(strategy_result)


if __name__ == "__main__":
    main()
