from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from backtest import calculate_strategy_equity
from data import download_price_data
from main import (
    CASH,
    END_DATE,
    INITIAL_CAPITAL,
    OUTPUT_DIR,
    START_DATE,
    TICKERS,
    TRADING_DAYS_PER_YEAR,
)
from metrics import calculate_performance_summary
from strategy import calculate_moving_average, get_month_end_trading_days


MOVING_AVERAGE_WINDOWS = [100, 150, 180, 200, 250]
MOMENTUM_LOOKBACK_DAYS = [30, 60, 90, 120]
HEATMAP_PATH = OUTPUT_DIR / "heatmap.png"
RESULTS_PATH = OUTPUT_DIR / "optimization_results.csv"


def calculate_momentum(prices: pd.DataFrame, lookback_days: int) -> pd.DataFrame:
    """计算给定回看周期的价格动量。"""
    return prices.pct_change(periods=lookback_days)


def generate_momentum_rebalance_signals(
    prices: pd.DataFrame,
    moving_average: pd.DataFrame,
    momentum: pd.DataFrame,
    cash: str,
) -> pd.Series:
    """用均线过滤风险后，在可投资资产中选择动量最高者。"""
    month_end_dates = get_month_end_trading_days(prices)
    signals = pd.Series(index=month_end_dates, dtype="object", name="rebalance_signal")

    for date in month_end_dates:
        eligible_assets: list[str] = []

        for ticker in TICKERS:
            price = prices.loc[date, ticker]
            moving_average_value = moving_average.loc[date, ticker]
            momentum_value = momentum.loc[date, ticker]

            if (
                not pd.isna(moving_average_value)
                and not pd.isna(momentum_value)
                and price >= moving_average_value
                and momentum_value > 0
            ):
                eligible_assets.append(ticker)

        if not eligible_assets:
            signals.loc[date] = cash
            continue

        signals.loc[date] = momentum.loc[date, eligible_assets].idxmax()

    return signals


def run_backtest_for_parameters(
    prices: pd.DataFrame,
    moving_average_window: int,
    momentum_lookback_days: int,
) -> pd.Series:
    """针对单个参数组合重新生成信号并跑完整回测。"""
    moving_average = calculate_moving_average(prices, moving_average_window)
    momentum = calculate_momentum(prices, momentum_lookback_days)
    rebalance_signals = generate_momentum_rebalance_signals(
        prices,
        moving_average,
        momentum,
        CASH,
    )
    strategy_result = calculate_strategy_equity(
        prices,
        rebalance_signals,
        INITIAL_CAPITAL,
        CASH,
    )
    return calculate_performance_summary(
        strategy_result,
        INITIAL_CAPITAL,
        TRADING_DAYS_PER_YEAR,
    )


def run_grid_search(prices: pd.DataFrame) -> pd.DataFrame:
    """执行均线窗口和动量回看周期的网格搜索。"""
    records: list[dict[str, float | int | str]] = []

    for moving_average_window in MOVING_AVERAGE_WINDOWS:
        for momentum_lookback_days in MOMENTUM_LOOKBACK_DAYS:
            summary = run_backtest_for_parameters(
                prices,
                moving_average_window,
                momentum_lookback_days,
            )
            records.append(
                {
                    "moving_average_window": moving_average_window,
                    "momentum_lookback_days": momentum_lookback_days,
                    "sharpe_ratio": summary["sharpe_ratio"],
                    "max_drawdown": summary["max_drawdown"],
                    "final_equity": summary["final_equity"],
                    "total_return": summary["total_return"],
                    "latest_position": summary["latest_position"],
                }
            )

    return pd.DataFrame.from_records(records)


def plot_sharpe_heatmap(results: pd.DataFrame, output_path: Path) -> None:
    """绘制不同参数组合下 Sharpe Ratio 的热力图。"""
    sharpe_matrix = results.pivot(
        index="moving_average_window",
        columns="momentum_lookback_days",
        values="sharpe_ratio",
    )

    figure, axis = plt.subplots(figsize=(9, 6))
    image = axis.imshow(sharpe_matrix, cmap="YlGnBu", aspect="auto")

    axis.set_title("Sharpe Ratio Heatmap")
    axis.set_xlabel("Momentum Lookback Days")
    axis.set_ylabel("Moving Average Window")
    axis.set_xticks(range(len(sharpe_matrix.columns)))
    axis.set_xticklabels(sharpe_matrix.columns)
    axis.set_yticks(range(len(sharpe_matrix.index)))
    axis.set_yticklabels(sharpe_matrix.index)

    for row_index, moving_average_window in enumerate(sharpe_matrix.index):
        for column_index, momentum_lookback_days in enumerate(sharpe_matrix.columns):
            value = sharpe_matrix.loc[moving_average_window, momentum_lookback_days]
            axis.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                color="black",
            )

    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Sharpe Ratio")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def main() -> None:
    """下载数据、执行网格搜索并保存 Sharpe 热力图。"""
    prices = download_price_data(TICKERS, START_DATE, END_DATE)
    results = run_grid_search(prices)

    OUTPUT_DIR.mkdir(exist_ok=True)
    results.to_csv(RESULTS_PATH, index=False)
    plot_sharpe_heatmap(results, HEATMAP_PATH)

    best_result = results.sort_values("sharpe_ratio", ascending=False).iloc[0]
    print("参数网格搜索完成")
    print(f"结果明细已保存到: {RESULTS_PATH.resolve()}")
    print(f"Sharpe 热力图已保存到: {HEATMAP_PATH.resolve()}")
    print(
        "最佳参数: "
        f"均线窗口={int(best_result['moving_average_window'])}, "
        f"动量回看={int(best_result['momentum_lookback_days'])} 天, "
        f"Sharpe={best_result['sharpe_ratio']:.2f}, "
        f"最大回撤={best_result['max_drawdown']:.2%}"
    )


if __name__ == "__main__":
    main()
