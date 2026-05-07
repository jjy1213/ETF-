from pathlib import Path

from backtest import calculate_strategy_equity, plot_equity_curve
from data import download_price_data, save_outputs
from metrics import calculate_annual_returns, calculate_performance_summary, print_summary
from report import generate_report
from strategy import calculate_moving_average, generate_rebalance_signals


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


def main() -> None:
    """主流程：下载数据 -> 计算均线 -> 月末调仓 -> 回测 -> 输出绩效。"""
    prices = download_price_data(TICKERS, START_DATE, END_DATE)
    moving_average = calculate_moving_average(prices, MOVING_AVERAGE_DAYS)
    rebalance_signals = generate_rebalance_signals(
        prices,
        moving_average,
        RISK_ASSET,
        DEFENSIVE_ASSET,
        CASH,
    )
    strategy_result = calculate_strategy_equity(
        prices,
        rebalance_signals,
        INITIAL_CAPITAL,
        CASH,
    )
    annual_returns = calculate_annual_returns(strategy_result, INITIAL_CAPITAL)
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
    plot_equity_curve(strategy_result["strategy_equity"], OUTPUT_DIR / "equity_curve.png")
    generate_report(
        strategy_result,
        prices,
        OUTPUT_DIR,
        RISK_ASSET,
        INITIAL_CAPITAL,
        TRADING_DAYS_PER_YEAR,
    )
    print_summary(str(OUTPUT_DIR.resolve()), annual_returns, performance_summary)


if __name__ == "__main__":
    main()
