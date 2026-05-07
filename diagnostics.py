from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from metrics import calculate_performance_summary, calculate_sharpe_ratio


ROLLING_SHARPE_CSV_NAME = "rolling_sharpe.csv"
ROLLING_SHARPE_PNG_NAME = "rolling_sharpe.png"
WALK_FORWARD_CSV_NAME = "walk_forward.csv"
WALK_FORWARD_TXT_NAME = "walk_forward.txt"


def calculate_rolling_sharpe(
    returns: pd.Series,
    window_days: int,
    trading_days_per_year: int,
) -> pd.Series:
    """计算滚动年化 Sharpe Ratio。"""
    rolling_mean = returns.rolling(window_days).mean()
    rolling_std = returns.rolling(window_days).std()
    rolling_sharpe = rolling_mean / rolling_std * (trading_days_per_year**0.5)
    rolling_sharpe = rolling_sharpe.replace([float("inf"), float("-inf")], pd.NA)
    rolling_sharpe.name = "rolling_sharpe"
    return rolling_sharpe


def save_rolling_sharpe(
    returns: pd.Series,
    output_dir: Path,
    window_days: int,
    trading_days_per_year: int,
) -> pd.Series:
    """保存 rolling Sharpe CSV 和图表。"""
    output_dir.mkdir(exist_ok=True)
    rolling_sharpe = calculate_rolling_sharpe(
        returns,
        window_days,
        trading_days_per_year,
    )
    rolling_sharpe.to_csv(output_dir / ROLLING_SHARPE_CSV_NAME, index_label="Date")

    plt.figure(figsize=(12, 6))
    plt.plot(rolling_sharpe.index, rolling_sharpe.values, label="Rolling Sharpe")
    plt.axhline(0, color="black", linewidth=1, alpha=0.5)
    plt.title(f"{window_days}-Day Rolling Sharpe Ratio")
    plt.xlabel("Date")
    plt.ylabel("Sharpe Ratio")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / ROLLING_SHARPE_PNG_NAME, dpi=150)
    plt.close()
    return rolling_sharpe


def build_walk_forward_report(
    strategy_result: pd.DataFrame,
    initial_capital: float,
    trading_days_per_year: int,
    min_train_years: int,
) -> pd.DataFrame:
    """按年份做 walk-forward 诊断；参数固定，不在训练段重新优化。"""
    years = sorted(strategy_result.index.year.unique())
    records: list[dict[str, float | int | str]] = []

    for test_year in years:
        train_years = [year for year in years if year < test_year]
        if len(train_years) < min_train_years:
            continue

        test_result = strategy_result.loc[str(test_year)].copy()
        if test_result.empty:
            continue

        test_returns = test_result["strategy_return"]
        test_equity = (1 + test_returns).cumprod() * initial_capital
        period_result = test_result.copy()
        period_result["strategy_equity"] = test_equity
        summary = calculate_performance_summary(
            period_result,
            initial_capital,
            trading_days_per_year,
        )

        records.append(
            {
                "train_start_year": train_years[0],
                "train_end_year": train_years[-1],
                "test_year": test_year,
                "test_total_return": summary["total_return"],
                "test_max_drawdown": summary["max_drawdown"],
                "test_sharpe_ratio": calculate_sharpe_ratio(
                    test_returns,
                    trading_days_per_year,
                ),
                "note": "fixed_parameters_no_in_sample_optimization",
            }
        )

    return pd.DataFrame.from_records(records)


def format_walk_forward_text(walk_forward: pd.DataFrame) -> str:
    """生成 walk-forward 纯文本摘要。"""
    lines = [
        "Walk-forward 测试报告",
        "参数固定，不在训练段或测试段重新优化，避免过度拟合。",
        "",
    ]

    for _, row in walk_forward.iterrows():
        lines.append(
            f"{int(row['train_start_year'])}-{int(row['train_end_year'])} -> "
            f"{int(row['test_year'])}: "
            f"收益 {row['test_total_return']:.2%}, "
            f"最大回撤 {row['test_max_drawdown']:.2%}, "
            f"Sharpe {row['test_sharpe_ratio']:.2f}"
        )

    return "\n".join(lines).rstrip() + "\n"


def save_walk_forward_report(
    strategy_result: pd.DataFrame,
    output_dir: Path,
    initial_capital: float,
    trading_days_per_year: int,
    min_train_years: int,
) -> pd.DataFrame:
    """保存 walk-forward CSV 和 TXT。"""
    output_dir.mkdir(exist_ok=True)
    walk_forward = build_walk_forward_report(
        strategy_result,
        initial_capital,
        trading_days_per_year,
        min_train_years,
    )
    walk_forward.to_csv(output_dir / WALK_FORWARD_CSV_NAME, index=False)
    (output_dir / WALK_FORWARD_TXT_NAME).write_text(
        format_walk_forward_text(walk_forward),
        encoding="utf-8",
    )
    return walk_forward
