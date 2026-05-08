from pathlib import Path

from backtest import (
    calculate_strategy_equity,
    plot_comparison_equity_curve,
)
from data import download_price_data, save_outputs
from diagnostics import save_rolling_sharpe, save_walk_forward_report
from generate_html_report import generate_integrated_report
from metrics import calculate_annual_returns, calculate_performance_summary, print_summary
from report import build_buy_hold_series, generate_report
from sensitivity import save_volatility_sensitivity
from strategy import (
    calculate_annual_holding_distribution,
    calculate_moving_average,
    generate_rebalance_signals,
)


# 策略参数：保持集中，方便初学者修改
TICKERS = ["QQQ", "SPY", "TLT"]
RISK_ASSET = "QQQ"
COMPARISON_ASSET = "SPY"
DEFENSIVE_ASSET = "TLT"
CASH = "CASH"
START_DATE = "2010-01-01"
END_DATE = None  # None 表示下载到最近一个交易日
MOVING_AVERAGE_DAYS = 200
MOMENTUM_LOOKBACK_DAYS = 60
TARGET_VOLATILITY = 0.10
VOLATILITY_LOOKBACK_DAYS = 20
MAX_POSITION_WEIGHT = 1.0
TRANSACTION_COST_BPS = 5.0
ROLLING_SHARPE_DAYS = 252
WALK_FORWARD_MIN_TRAIN_YEARS = 3
INITIAL_CAPITAL = 1.0
TRADING_DAYS_PER_YEAR = 252
OUTPUT_DIR = Path("outputs")


def main() -> None:
    """主流程：下载数据 -> 计算均线 -> 月末调仓 -> 回测 -> 输出绩效。"""
    prices = download_price_data(
        TICKERS,
        START_DATE,
        END_DATE,
        cache_path=OUTPUT_DIR / "prices.csv",
    )
    moving_average = calculate_moving_average(prices, MOVING_AVERAGE_DAYS)
    rebalance_signals = generate_rebalance_signals(
        prices,
        moving_average,
        RISK_ASSET,
        DEFENSIVE_ASSET,
        CASH,
        comparison_asset=COMPARISON_ASSET,
        momentum_lookback_days=MOMENTUM_LOOKBACK_DAYS,
    )
    strategy_result = calculate_strategy_equity(
        prices,
        rebalance_signals,
        INITIAL_CAPITAL,
        CASH,
    )
    annual_returns_for_print = calculate_annual_returns(strategy_result, INITIAL_CAPITAL)
    holding_distribution = calculate_annual_holding_distribution(
        rebalance_signals,
        [RISK_ASSET, COMPARISON_ASSET, DEFENSIVE_ASSET],
        CASH,
    )
    annual_returns = annual_returns_for_print.join(holding_distribution, how="left")
    performance_summary = calculate_performance_summary(
        strategy_result,
        INITIAL_CAPITAL,
        TRADING_DAYS_PER_YEAR,
    )

    save_outputs(
        OUTPUT_DIR,
        prices,
        moving_average,
        rebalance_signals,
        strategy_result,
        annual_returns,
        performance_summary,
    )
    _, benchmark_equity = build_buy_hold_series(prices, RISK_ASSET, INITIAL_CAPITAL)
    plot_comparison_equity_curve(
        strategy_result["strategy_equity"],
        benchmark_equity,
        OUTPUT_DIR / "equity_curve.png",
    )
    generate_report(
        strategy_result,
        prices,
        OUTPUT_DIR,
        RISK_ASSET,
        INITIAL_CAPITAL,
        TRADING_DAYS_PER_YEAR,
    )
    save_volatility_sensitivity(
        prices,
        rebalance_signals,
        OUTPUT_DIR,
        INITIAL_CAPITAL,
        CASH,
        TRADING_DAYS_PER_YEAR,
        MAX_POSITION_WEIGHT,
        TRANSACTION_COST_BPS,
    )
    save_rolling_sharpe(
        strategy_result["strategy_return"],
        OUTPUT_DIR,
        ROLLING_SHARPE_DAYS,
        TRADING_DAYS_PER_YEAR,
    )
    save_walk_forward_report(
        strategy_result,
        OUTPUT_DIR,
        INITIAL_CAPITAL,
        TRADING_DAYS_PER_YEAR,
        WALK_FORWARD_MIN_TRAIN_YEARS,
    )
    generate_integrated_report(OUTPUT_DIR)
    print_summary(str(OUTPUT_DIR.resolve()), annual_returns_for_print, performance_summary)


if __name__ == "__main__":
    main()
