import pandas as pd


def calculate_moving_average(prices: pd.DataFrame, window_days: int) -> pd.DataFrame:
    """计算 N 日移动平均线。"""
    return prices.rolling(window=window_days).mean()


def calculate_momentum(prices: pd.DataFrame, lookback_days: int) -> pd.DataFrame:
    """计算给定回看期的价格动量。"""
    return prices.pct_change(periods=lookback_days)


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
    comparison_asset: str | None = None,
    momentum_lookback_days: int = 60,
) -> pd.Series:
    """
    在每月最后一个交易日生成调仓信号。

    规则：
    1. 默认保持原 QQQ/TLT 200MA 逻辑。
    2. 如果传入 comparison_asset，则先比较 risk_asset 和 comparison_asset
       的 60 日动量，选择更强的权益资产作为候选。
    3. 候选权益资产高于 200MA 时持有它，否则检查防御资产。
    4. 如果防御资产也低于 200MA，则持有现金。
    """
    month_end_dates = get_month_end_trading_days(prices)
    signals = pd.Series(index=month_end_dates, dtype="object", name="rebalance_signal")
    momentum = calculate_momentum(prices, momentum_lookback_days)

    for date in month_end_dates:
        # 新增 SPY 候选：每月末先比较 QQQ 与 SPY 的 60 日动量。
        if comparison_asset is not None:
            risk_momentum = momentum.loc[date, risk_asset]
            comparison_momentum = momentum.loc[date, comparison_asset]

            if pd.isna(risk_momentum) or pd.isna(comparison_momentum):
                signals.loc[date] = cash
                continue

            candidate_asset = (
                risk_asset if risk_momentum >= comparison_momentum else comparison_asset
            )
        else:
            candidate_asset = risk_asset

        candidate_price = prices.loc[date, candidate_asset]
        candidate_ma = moving_average.loc[date, candidate_asset]
        defensive_price = prices.loc[date, defensive_asset]
        defensive_ma = moving_average.loc[date, defensive_asset]

        # 200 日均线数据不足时，保守地保持现金。
        if pd.isna(candidate_ma):
            signals.loc[date] = cash
        elif candidate_price >= candidate_ma:
            signals.loc[date] = candidate_asset
        elif not pd.isna(defensive_ma) and defensive_price >= defensive_ma:
            signals.loc[date] = defensive_asset
        else:
            signals.loc[date] = cash

    return signals


def calculate_annual_holding_distribution(
    rebalance_signals: pd.Series,
    assets: list[str],
    cash: str,
) -> pd.DataFrame:
    """统计每年各持仓信号出现的月数，供年度收益表展示持仓分布。"""
    rows: list[dict[str, int | str]] = []

    for year, yearly_signals in rebalance_signals.groupby(rebalance_signals.index.year):
        counts = yearly_signals.value_counts()
        distribution = {
            asset: int(counts.get(asset, 0))
            for asset in [*assets, cash]
        }
        rows.append(
            {
                "year": int(year),
                "holding_distribution": " / ".join(
                    f"{asset}:{months}个月" for asset, months in distribution.items()
                ),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["holding_distribution"])

    distribution_df = pd.DataFrame(rows).set_index("year")
    distribution_df.index.name = "year"
    return distribution_df


def generate_rotation_rebalance_weights(
    prices: pd.DataFrame,
    moving_average: pd.DataFrame,
    momentum: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    """在月末选择站上均线且动量最高的 ETF，生成等权目标权重。"""
    month_end_dates = get_month_end_trading_days(prices)
    weights = pd.DataFrame(0.0, index=month_end_dates, columns=prices.columns)
    weights.index.name = "Date"

    for date in month_end_dates:
        trend_filter = prices.loc[date] >= moving_average.loc[date]
        valid_momentum = momentum.loc[date].dropna()
        eligible_assets = valid_momentum[
            trend_filter.reindex(valid_momentum.index).fillna(False)
            & (valid_momentum > 0)
        ]

        selected_assets = eligible_assets.sort_values(ascending=False).head(top_n).index
        if len(selected_assets) == 0:
            continue

        weights.loc[date, selected_assets] = 1.0 / len(selected_assets)

    return weights
