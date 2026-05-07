import pandas as pd


def calculate_moving_average(prices: pd.DataFrame, window_days: int) -> pd.DataFrame:
    """计算 N 日移动平均线。"""
    return prices.rolling(window=window_days).mean()


def get_month_end_trading_days(prices: pd.DataFrame) -> pd.DatetimeIndex:
    """找出每个月的最后一个交易日，并避免把未结束的当月误判为月末。"""
    months = prices.index.to_period("M")
    is_month_end = months[:-1] != months[1:]
    month_end_dates = list(prices.index[:-1][is_month_end])

    # 如果最后一条数据本身就是自然月最后一个工作日，也可以作为月末调仓日。
    last_date = prices.index[-1]
    if pd.offsets.BMonthEnd().is_on_offset(last_date):
        month_end_dates.append(last_date)

    return pd.DatetimeIndex(month_end_dates)


def generate_rebalance_signals(
    prices: pd.DataFrame,
    moving_average: pd.DataFrame,
    risk_asset: str,
    defensive_asset: str,
    cash: str,
) -> pd.Series:
    """
    在每月最后一个交易日生成调仓信号。

    规则：
    1. 风险资产在 200 日均线上方时，持有风险资产。
    2. 风险资产低于 200 日均线时，切换到防御资产。
    3. 如果防御资产也低于 200 日均线，则持有现金。
    """
    month_end_dates = get_month_end_trading_days(prices)
    signals = pd.Series(index=month_end_dates, dtype="object", name="rebalance_signal")

    for date in month_end_dates:
        risk_price = prices.loc[date, risk_asset]
        risk_ma = moving_average.loc[date, risk_asset]
        defensive_price = prices.loc[date, defensive_asset]
        defensive_ma = moving_average.loc[date, defensive_asset]

        # 200 日均线数据不足时，保守地保持现金。
        if pd.isna(risk_ma):
            signals.loc[date] = cash
        elif risk_price >= risk_ma:
            signals.loc[date] = risk_asset
        elif not pd.isna(defensive_ma) and defensive_price >= defensive_ma:
            signals.loc[date] = defensive_asset
        else:
            signals.loc[date] = cash

    return signals
