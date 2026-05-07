import pandas as pd


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


def calculate_sharpe_ratio(returns: pd.Series, trading_days_per_year: int) -> float:
    """计算年化 Sharpe Ratio，这里假设无风险利率为 0。"""
    return_std = returns.std()
    if return_std == 0:
        return 0.0
    return float(returns.mean() / return_std * (trading_days_per_year**0.5))


def calculate_performance_summary(
    strategy_result: pd.DataFrame,
    initial_capital: float,
    trading_days_per_year: int,
) -> pd.Series:
    """汇总核心绩效指标。"""
    equity = strategy_result["strategy_equity"]
    returns = strategy_result["strategy_return"]
    final_equity = equity.iloc[-1]

    return pd.Series(
        {
            "final_equity": final_equity,
            "total_return": final_equity / initial_capital - 1,
            "max_drawdown": calculate_max_drawdown(equity),
            "sharpe_ratio": calculate_sharpe_ratio(returns, trading_days_per_year),
            "latest_position": strategy_result["position"].iloc[-1],
        },
        name="value",
    )


def print_summary(
    output_dir: str,
    annual_returns: pd.DataFrame,
    performance_summary: pd.Series,
) -> None:
    """在终端打印简要结果。"""
    print("月末 200MA 波动率仓位管理策略回测完成")
    print(f"最新持仓信号: {performance_summary['latest_position']}")
    print(f"最终资金曲线值: {performance_summary['final_equity']:.4f}")
    print(f"累计收益率: {performance_summary['total_return']:.2%}")
    print(f"最大回撤: {performance_summary['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {performance_summary['sharpe_ratio']:.2f}")
    print("\n每年收益率:")
    print(annual_returns.map(lambda value: f"{value:.2%}").to_string())
    print(f"结果文件已保存到: {output_dir}")
