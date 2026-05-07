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


def build_position_label(weights: pd.DataFrame, cash: str) -> pd.Series:
    """把每日权重转换为便于阅读的持仓标签。"""
    labels = []
    for _, row in weights.iterrows():
        held_assets = [ticker for ticker, weight in row.items() if weight > 0]
        labels.append(",".join(held_assets) if held_assets else cash)

    return pd.Series(labels, index=weights.index, name="position")


def scale_rebalance_weights_by_volatility(
    prices: pd.DataFrame,
    rebalance_weights: pd.DataFrame,
    target_volatility: float,
    volatility_lookback_days: int,
    trading_days_per_year: int,
    max_gross_exposure: float,
) -> pd.DataFrame:
    """在月末用历史波动率估计组合风险，并缩放目标权重。"""
    daily_returns = prices.pct_change().fillna(0)
    annualized_volatility = daily_returns.rolling(volatility_lookback_days).std() * (
        trading_days_per_year**0.5
    )
    scaled_weights = rebalance_weights.copy()

    for date, weights in rebalance_weights.iterrows():
        selected_weights = weights[weights > 0]
        if selected_weights.empty:
            continue

        selected_volatility = annualized_volatility.loc[date, selected_weights.index]
        if selected_volatility.isna().any() or (selected_volatility <= 0).any():
            scaled_weights.loc[date] = 0.0
            continue

        # Correlations are intentionally ignored to avoid fitting a covariance model.
        portfolio_volatility = (
            (selected_weights * selected_volatility) ** 2
        ).sum() ** 0.5
        exposure_scale = min(max_gross_exposure, target_volatility / portfolio_volatility)
        scaled_weights.loc[date] = weights * exposure_scale

    return scaled_weights


def build_daily_target_weights(
    rebalance_weights: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
) -> pd.DataFrame:
    """月末信号在下一交易日执行，并在两次调仓之间保持权重不变。"""
    daily_weights = rebalance_weights.reindex(trading_days).ffill().fillna(0.0)
    return daily_weights.shift(1).fillna(0.0)


def calculate_rotation_strategy_equity(
    prices: pd.DataFrame,
    rebalance_weights: pd.DataFrame,
    initial_capital: float,
    cash: str,
    target_volatility: float,
    volatility_lookback_days: int,
    trading_days_per_year: int,
    max_gross_exposure: float,
    transaction_cost_bps: float,
) -> pd.DataFrame:
    """计算多 ETF 月度轮动、波动率控仓和交易成本后的资金曲线。"""
    daily_returns = prices.pct_change().fillna(0)
    scaled_rebalance_weights = scale_rebalance_weights_by_volatility(
        prices,
        rebalance_weights,
        target_volatility,
        volatility_lookback_days,
        trading_days_per_year,
        max_gross_exposure,
    )
    daily_weights = build_daily_target_weights(
        scaled_rebalance_weights,
        daily_returns.index,
    )
    turnover = daily_weights.diff().abs().sum(axis=1).fillna(daily_weights.abs().sum(axis=1))
    transaction_cost = turnover * (transaction_cost_bps / 10_000)
    gross_return = (daily_weights * daily_returns).sum(axis=1)
    strategy_returns = gross_return - transaction_cost
    strategy_returns.name = "strategy_return"
    equity_curve = (1 + strategy_returns).cumprod() * initial_capital
    equity_curve.name = "strategy_equity"

    result = pd.DataFrame(
        {
            "rebalance_signal": build_position_label(
                scaled_rebalance_weights.reindex(daily_returns.index),
                cash,
            ),
            "position": build_position_label(daily_weights, cash),
            "gross_exposure": daily_weights.sum(axis=1),
            "turnover": turnover,
            "transaction_cost": transaction_cost,
            "gross_return": gross_return,
            "strategy_return": strategy_returns,
            "strategy_equity": equity_curve,
        }
    )

    for ticker in prices.columns:
        result[f"weight_{ticker}"] = daily_weights[ticker]

    return result


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
    plt.plot(strategy_equity.index, strategy_equity.values, label="Multi-ETF Rotation")
    plt.plot(benchmark_equity.index, benchmark_equity.values, label="QQQ Buy & Hold")
    plt.title("Multi-ETF 200MA Rotation vs QQQ Buy & Hold")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
