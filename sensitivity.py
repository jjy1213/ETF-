from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from backtest import calculate_rotation_strategy_equity
from metrics import calculate_performance_summary


TARGET_VOLATILITY_GRID = [0.08, 0.10, 0.12, 0.14, 0.16]
VOLATILITY_LOOKBACK_GRID = [20, 40, 63, 90, 120]
SENSITIVITY_CSV_NAME = "volatility_sensitivity.csv"
SHARPE_HEATMAP_NAME = "volatility_sensitivity_sharpe.png"
DRAWDOWN_HEATMAP_NAME = "volatility_sensitivity_drawdown.png"


def run_volatility_sensitivity(
    prices: pd.DataFrame,
    rebalance_weights: pd.DataFrame,
    initial_capital: float,
    cash: str,
    trading_days_per_year: int,
    max_position_weight: float,
    transaction_cost_bps: float,
) -> pd.DataFrame:
    """用固定网格评估波动率仓位参数敏感性。"""
    records: list[dict[str, float | int]] = []

    for volatility_lookback_days in VOLATILITY_LOOKBACK_GRID:
        for target_volatility in TARGET_VOLATILITY_GRID:
            strategy_result = calculate_rotation_strategy_equity(
                prices,
                rebalance_weights,
                initial_capital,
                cash,
                target_volatility,
                volatility_lookback_days,
                trading_days_per_year,
                max_position_weight,
                transaction_cost_bps,
            )
            summary = calculate_performance_summary(
                strategy_result,
                initial_capital,
                trading_days_per_year,
            )
            records.append(
                {
                    "volatility_lookback_days": volatility_lookback_days,
                    "target_volatility": target_volatility,
                    "sharpe_ratio": summary["sharpe_ratio"],
                    "max_drawdown": summary["max_drawdown"],
                    "total_return": summary["total_return"],
                    "final_equity": summary["final_equity"],
                }
            )

    return pd.DataFrame.from_records(records)


def plot_sensitivity_heatmap(
    results: pd.DataFrame,
    metric: str,
    title: str,
    colorbar_label: str,
    output_path: Path,
) -> None:
    """绘制波动率参数敏感性热力图。"""
    matrix = results.pivot(
        index="volatility_lookback_days",
        columns="target_volatility",
        values=metric,
    )

    figure, axis = plt.subplots(figsize=(9, 6))
    image = axis.imshow(matrix, cmap="YlGnBu", aspect="auto")
    axis.set_title(title)
    axis.set_xlabel("Target Volatility")
    axis.set_ylabel("Volatility Lookback Days")
    axis.set_xticks(range(len(matrix.columns)))
    axis.set_xticklabels([f"{value:.0%}" for value in matrix.columns])
    axis.set_yticks(range(len(matrix.index)))
    axis.set_yticklabels(matrix.index)

    for row_index, lookback in enumerate(matrix.index):
        for column_index, target_volatility in enumerate(matrix.columns):
            value = matrix.loc[lookback, target_volatility]
            label = f"{value:.2f}" if metric == "sharpe_ratio" else f"{value:.1%}"
            axis.text(
                column_index,
                row_index,
                label,
                ha="center",
                va="center",
                color="black",
            )

    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label(colorbar_label)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def save_volatility_sensitivity(
    prices: pd.DataFrame,
    rebalance_weights: pd.DataFrame,
    output_dir: Path,
    initial_capital: float,
    cash: str,
    trading_days_per_year: int,
    max_position_weight: float,
    transaction_cost_bps: float,
) -> pd.DataFrame:
    """保存波动率参数敏感性 CSV 和热力图。"""
    output_dir.mkdir(exist_ok=True)
    results = run_volatility_sensitivity(
        prices,
        rebalance_weights,
        initial_capital,
        cash,
        trading_days_per_year,
        max_position_weight,
        transaction_cost_bps,
    )
    results.to_csv(output_dir / SENSITIVITY_CSV_NAME, index=False)
    plot_sensitivity_heatmap(
        results,
        "sharpe_ratio",
        "Volatility Sizing Sharpe Sensitivity",
        "Sharpe Ratio",
        output_dir / SHARPE_HEATMAP_NAME,
    )
    plot_sensitivity_heatmap(
        results,
        "max_drawdown",
        "Volatility Sizing Max Drawdown Sensitivity",
        "Max Drawdown",
        output_dir / DRAWDOWN_HEATMAP_NAME,
    )
    return results
