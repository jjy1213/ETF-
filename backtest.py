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


def calculate_volatility_managed_strategy_equity(
    prices: pd.DataFrame,
    rebalance_signals: pd.Series,
    initial_capital: float,
    cash: str,
    target_volatility: float,
    volatility_lookback_days: int,
    trading_days_per_year: int,
    max_position_weight: float,
) -> pd.DataFrame:
    """用目标波动率缩放每日仓位，剩余资金持现金，不使用杠杆。"""
    daily_returns = prices.pct_change().fillna(0)
    positions = build_daily_positions(rebalance_signals, daily_returns.index, cash)
    annualized_volatility = (
        daily_returns.rolling(volatility_lookback_days).std().shift(1)
        * (trading_days_per_year**0.5)
    )

    position_weights = pd.Series(0.0, index=daily_returns.index, name="position_weight")
    strategy_returns = pd.Series(0.0, index=daily_returns.index, name="strategy_return")

    for ticker in prices.columns:
        ticker_volatility = annualized_volatility[ticker].replace(0, pd.NA)
        ticker_weights = (target_volatility / ticker_volatility).clip(
            lower=0.0,
            upper=max_position_weight,
        )
        ticker_weights = ticker_weights.fillna(0.0)

        ticker_mask = positions == ticker
        position_weights.loc[ticker_mask] = ticker_weights.loc[ticker_mask]
        strategy_returns.loc[ticker_mask] = (
            ticker_weights.loc[ticker_mask] * daily_returns.loc[ticker_mask, ticker]
        )

    equity_curve = (1 + strategy_returns).cumprod() * initial_capital
    equity_curve.name = "strategy_equity"

    return pd.DataFrame(
        {
            "rebalance_signal": rebalance_signals.reindex(daily_returns.index),
            "position": positions,
            "position_weight": position_weights,
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


def plot_comparison_equity_curve(
    strategy_equity: pd.Series,
    benchmark_equity: pd.Series,
    output_path: Path,
) -> None:
    """绘制策略与基准买入持有的资金曲线。"""
    plt.figure(figsize=(12, 6))
    plt.plot(strategy_equity.index, strategy_equity.values, label="200MA Vol Managed")
    plt.plot(benchmark_equity.index, benchmark_equity.values, label="QQQ Buy & Hold")
    plt.title("200MA Vol Managed Strategy vs QQQ Buy & Hold")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
