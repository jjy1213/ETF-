from pathlib import Path

import pandas as pd

from metrics import calculate_max_drawdown, calculate_sharpe_ratio


REPORT_CSV_NAME = "report.csv"
REPORT_TXT_NAME = "report.txt"


def calculate_annualized_return(equity: pd.Series) -> float:
    """按回测首尾日期计算年化收益率。"""
    if len(equity) < 2:
        return 0.0

    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0:
        return 0.0

    total_return = equity.iloc[-1] / equity.iloc[0]
    return float(total_return ** (1 / years) - 1)


def calculate_monthly_returns(returns: pd.Series) -> pd.Series:
    """把日收益率复合为月度收益率。"""
    return (1 + returns).resample("ME").prod() - 1


def calculate_monthly_win_rate(monthly_returns: pd.Series) -> float:
    """计算月度胜率。"""
    valid_returns = monthly_returns.dropna()
    if valid_returns.empty:
        return 0.0

    return float((valid_returns > 0).mean())


def calculate_profit_loss_ratio(monthly_returns: pd.Series) -> float:
    """计算月度平均盈利与平均亏损绝对值之比。"""
    winning_returns = monthly_returns[monthly_returns > 0]
    losing_returns = monthly_returns[monthly_returns < 0]

    if winning_returns.empty:
        return 0.0
    if losing_returns.empty:
        return float("inf")

    return float(winning_returns.mean() / abs(losing_returns.mean()))


def calculate_report_metrics(
    equity: pd.Series,
    returns: pd.Series,
    trading_days_per_year: int,
) -> dict[str, float]:
    """汇总单个资金曲线的报告指标。"""
    monthly_returns = calculate_monthly_returns(returns)

    return {
        "annualized_return": calculate_annualized_return(equity),
        "max_drawdown": calculate_max_drawdown(equity),
        "sharpe_ratio": calculate_sharpe_ratio(returns, trading_days_per_year),
        "monthly_win_rate": calculate_monthly_win_rate(monthly_returns),
        "profit_loss_ratio": calculate_profit_loss_ratio(monthly_returns),
    }


def build_buy_hold_series(
    prices: pd.DataFrame,
    benchmark_ticker: str,
    initial_capital: float,
) -> tuple[pd.Series, pd.Series]:
    """构造基准买入持有的每日收益和资金曲线。"""
    benchmark_returns = prices[benchmark_ticker].pct_change().fillna(0)
    benchmark_returns.name = "benchmark_return"

    benchmark_equity = (1 + benchmark_returns).cumprod() * initial_capital
    benchmark_equity.name = "benchmark_equity"
    return benchmark_returns, benchmark_equity


def build_report(
    strategy_result: pd.DataFrame,
    prices: pd.DataFrame,
    benchmark_ticker: str,
    initial_capital: float,
    trading_days_per_year: int,
) -> pd.DataFrame:
    """生成策略与基准买入持有的对比报告。"""
    benchmark_returns, benchmark_equity = build_buy_hold_series(
        prices,
        benchmark_ticker,
        initial_capital,
    )

    records = {
        "strategy": calculate_report_metrics(
            strategy_result["strategy_equity"],
            strategy_result["strategy_return"],
            trading_days_per_year,
        ),
        f"{benchmark_ticker}_buy_hold": calculate_report_metrics(
            benchmark_equity,
            benchmark_returns,
            trading_days_per_year,
        ),
    }

    report = pd.DataFrame.from_dict(records, orient="index")
    report.index.name = "portfolio"
    return report


def format_percent(value: float) -> str:
    """把小数格式化为百分比文本。"""
    return f"{value:.2%}"


def format_number(value: float) -> str:
    """把普通数值格式化为两位小数文本。"""
    if value == float("inf"):
        return "inf"
    return f"{value:.2f}"


def format_report_text(report: pd.DataFrame) -> str:
    """生成适合阅读的纯文本报告。"""
    lines = ["策略 vs QQQ 买入持有对比报告", ""]
    metric_labels = {
        "annualized_return": "年化收益率",
        "max_drawdown": "最大回撤",
        "sharpe_ratio": "Sharpe Ratio",
        "monthly_win_rate": "胜率（月度）",
        "profit_loss_ratio": "盈亏比",
    }

    for portfolio, row in report.iterrows():
        lines.append(f"[{portfolio}]")
        lines.append(
            f"{metric_labels['annualized_return']}: "
            f"{format_percent(row['annualized_return'])}"
        )
        lines.append(
            f"{metric_labels['max_drawdown']}: {format_percent(row['max_drawdown'])}"
        )
        lines.append(
            f"{metric_labels['sharpe_ratio']}: {format_number(row['sharpe_ratio'])}"
        )
        lines.append(
            f"{metric_labels['monthly_win_rate']}: "
            f"{format_percent(row['monthly_win_rate'])}"
        )
        lines.append(
            f"{metric_labels['profit_loss_ratio']}: "
            f"{format_number(row['profit_loss_ratio'])}"
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def save_report(report: pd.DataFrame, output_dir: Path) -> None:
    """保存 CSV 和 TXT 两种格式的报告。"""
    output_dir.mkdir(exist_ok=True)
    report.to_csv(output_dir / REPORT_CSV_NAME)
    (output_dir / REPORT_TXT_NAME).write_text(
        format_report_text(report),
        encoding="utf-8",
    )


def generate_report(
    strategy_result: pd.DataFrame,
    prices: pd.DataFrame,
    output_dir: Path,
    benchmark_ticker: str,
    initial_capital: float,
    trading_days_per_year: int,
) -> pd.DataFrame:
    """生成并保存策略与基准买入持有的对比报告。"""
    report = build_report(
        strategy_result,
        prices,
        benchmark_ticker,
        initial_capital,
        trading_days_per_year,
    )
    save_report(report, output_dir)
    return report
