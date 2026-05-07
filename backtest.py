from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def build_daily_positions(
    rebalance_signals: pd.Series,
    trading_days: pd.DatetimeIndex,
    cash: str,
) -> pd.Series:
    """把月末调仓信号扩展为每日持仓。"""
    daily_signal = rebalance_signals.reindex(trading_days).ffill()

    # 月末收盘后得到信号，下一交易日才执行，避免未来函数。
    positions = daily_signal.shift(1).fillna(cash)
    positions.name = "position"
    return positions


def calculate_strategy_equity(
    prices: pd.DataFrame,
    rebalance_signals: pd.Series,
    initial_capital: float,
    cash: str,
) -> pd.DataFrame:
    """根据持仓信号计算策略每日收益和资金曲线。"""
    daily_returns = prices.pct_change().fillna(0)
    positions = build_daily_positions(rebalance_signals, daily_returns.index, cash)

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
