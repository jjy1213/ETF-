from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


# 策略参数：保持集中，方便初学者修改
TICKERS = ["QQQ", "TLT"]
RISK_ASSET = "QQQ"
DEFENSIVE_ASSET = "TLT"
CASH = "CASH"
START_DATE = "2010-01-01"
END_DATE = None  # None 表示下载到最近一个交易日
MOVING_AVERAGE_DAYS = 200
INITIAL_CAPITAL = 1.0
TRADING_DAYS_PER_YEAR = 252
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


def calculate_moving_average(prices: pd.DataFrame, window_days: int) -> pd.DataFrame:
    """计算 N 日移动平均线。"""
    return prices.rolling(window=window_days).mean()


def get_month_end_trading_days(prices: pd.DataFrame) -> pd.DatetimeIndex:
    """找出每个月的最后一个交易日。"""
    return prices.groupby(prices.index.to_period("M")).tail(1).index


def generate_rebalance_signals(
    prices: pd.DataFrame,
    moving_average: pd.DataFrame,
) -> pd.Series:
    """
    在每月最后一个交易日生成调仓信号。

    规则：
    1. QQQ 在 200 日均线上方时，持有 QQQ。
    2. QQQ 低于 200 日均线时，切换到 TLT。
    3. 如果 TLT 也低于 200 日均线，则持有现金。
    """
    month_end_dates = get_month_end_trading_days(prices)
    signals = pd.Series(index=month_end_dates, dtype="object", name="rebalance_signal")

    for date in month_end_dates:
        qqq_price = prices.loc[date, RISK_ASSET]
        qqq_ma = moving_average.loc[date, RISK_ASSET]
        tlt_price = prices.loc[date, DEFENSIVE_ASSET]
        tlt_ma = moving_average.loc[date, DEFENSIVE_ASSET]

        # 200 日均线数据不足时，保守地保持现金。
        if pd.isna(qqq_ma):
            signals.loc[date] = CASH
        elif qqq_price >= qqq_ma:
            signals.loc[date] = RISK_ASSET
        elif not pd.isna(tlt_ma) and tlt_price >= tlt_ma:
            signals.loc[date] = DEFENSIVE_ASSET
        else:
            signals.loc[date] = CASH

    return signals


def build_daily_positions(
    rebalance_signals: pd.Series,
    trading_days: pd.DatetimeIndex,
) -> pd.Series:
    """把月末调仓信号扩展为每日持仓。"""
    daily_signal = rebalance_signals.reindex(trading_days).ffill()

    # 月末收盘后得到信号，下一交易日才执行，避免未来函数。
    positions = daily_signal.shift(1).fillna(CASH)
    positions.name = "position"
    return positions


def calculate_strategy_equity(
    prices: pd.DataFrame,
    rebalance_signals: pd.Series,
    initial_capital: float,
) -> pd.DataFrame:
    """根据持仓信号计算策略每日收益和资金曲线。"""
    daily_returns = prices.pct_change().fillna(0)
    positions = build_daily_positions(rebalance_signals, daily_returns.index)

    strategy_returns = pd.Series(0.0, index=daily_returns.index, name="strategy_return")
    for ticker in prices.columns:
        strategy_returns.loc[positions == ticker] = daily_returns.loc[positions == ticker, ticker]

    equity_curve = (1 + strategy_returns).cumprod() * initial_capital
    equity_curve.name = "strategy_equity"

    return pd.DataFrame(
        {
            "rebalance_signal": rebalance_signals.reindex(daily_returns.index),
            "position": positions,
            "strategy_return": strategy_returns,
            "strategy_equity": equity_curve,
        }
    )


def calculate_annual_returns(
    strategy_result: pd.DataFrame,
    initial_capital: float,
) -> pd.DataFrame:
    """计算每年收益率。"""
    year_end_equity = strategy_result["strategy_equity"].resample("YE").last()
    annual_returns = year_end_equity.pct_change()

    if not annual_returns.empty:
        annual_returns.iloc[0] = year_end_equity.iloc[0] / initial_capital - 1

    annual_returns.index = annual_returns.index.year
    annual_returns.index.name = "year"
    return annual_returns.to_frame(name="annual_return")


def calculate_max_drawdown(equity: pd.Series) -> float:
    """计算最大回撤。"""
    drawdown = equity / equity.cummax() - 1
    return float(drawdown.min())


def calculate_sharpe_ratio(returns: pd.Series) -> float:
    """计算年化 Sharpe Ratio，这里假设无风险利率为 0。"""
    return_std = returns.std()
    if return_std == 0:
        return 0.0
    return float(returns.mean() / return_std * (TRADING_DAYS_PER_YEAR**0.5))


def calculate_performance_summary(strategy_result: pd.DataFrame) -> pd.Series:
    """汇总核心绩效指标。"""
    equity = strategy_result["strategy_equity"]
    returns = strategy_result["strategy_return"]
    final_equity = equity.iloc[-1]

    return pd.Series(
        {
            "final_equity": final_equity,
            "total_return": final_equity / INITIAL_CAPITAL - 1,
            "max_drawdown": calculate_max_drawdown(equity),
            "sharpe_ratio": calculate_sharpe_ratio(returns),
            "latest_position": strategy_result["position"].iloc[-1],
        },
        name="value",
    )


def plot_equity_curve(equity: pd.Series, output_path: Path) -> None:
    """绘制并保存策略资金曲线。"""
    plt.figure(figsize=(12, 6))
    plt.plot(equity.index, equity.values, label="Monthly 200MA Strategy", linewidth=2)
    plt.title("QQQ/TLT Monthly 200MA Strategy Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def save_outputs(
    prices: pd.DataFrame,
    moving_average: pd.DataFrame,
    rebalance_signals: pd.Series,
    strategy_result: pd.DataFrame,
    annual_returns: pd.DataFrame,
    performance_summary: pd.Series,
) -> None:
    """保存研究结果，方便后续检查和复盘。"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    prices.to_csv(OUTPUT_DIR / "prices.csv")
    moving_average.to_csv(OUTPUT_DIR / "moving_average.csv")
    rebalance_signals.to_csv(OUTPUT_DIR / "rebalance_signals.csv")
    strategy_result.to_csv(OUTPUT_DIR / "strategy_result.csv")
    strategy_result[["rebalance_signal", "position"]].to_csv(OUTPUT_DIR / "signals.csv")
    annual_returns.to_csv(OUTPUT_DIR / "annual_returns.csv")
    performance_summary.to_csv(OUTPUT_DIR / "performance_summary.csv")
    plot_equity_curve(strategy_result["strategy_equity"], OUTPUT_DIR / "equity_curve.png")


def print_summary(
    annual_returns: pd.DataFrame,
    performance_summary: pd.Series,
) -> None:
    """在终端打印简要结果。"""
    print("月末 200MA 风险过滤策略回测完成")
    print(f"最新持仓信号: {performance_summary['latest_position']}")
    print(f"最终资金曲线值: {performance_summary['final_equity']:.4f}")
    print(f"累计收益率: {performance_summary['total_return']:.2%}")
    print(f"最大回撤: {performance_summary['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {performance_summary['sharpe_ratio']:.2f}")
    print("\n每年收益率:")
    print(annual_returns.map(lambda value: f"{value:.2%}").to_string())
    print(f"结果文件已保存到: {OUTPUT_DIR.resolve()}")


def main() -> None:
    """主流程：下载数据 -> 计算均线 -> 月末调仓 -> 回测 -> 输出绩效。"""
    prices = download_price_data(TICKERS, START_DATE, END_DATE)
    moving_average = calculate_moving_average(prices, MOVING_AVERAGE_DAYS)
    rebalance_signals = generate_rebalance_signals(prices, moving_average)
    strategy_result = calculate_strategy_equity(prices, rebalance_signals, INITIAL_CAPITAL)
    annual_returns = calculate_annual_returns(strategy_result, INITIAL_CAPITAL)
    performance_summary = calculate_performance_summary(strategy_result)

    save_outputs(
        prices,
        moving_average,
        rebalance_signals,
        strategy_result,
        annual_returns,
        performance_summary,
    )
    print_summary(annual_returns, performance_summary)


if __name__ == "__main__":
    main()
