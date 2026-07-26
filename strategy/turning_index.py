import pandas as pd


def build_turning_index(
    theme_prices: pd.DataFrame,
    rank_return_window: int = 21,
    rank_change_lag: int = 21,
    rank_vol_window: int = 220,
    smooth_window: int = 20,
) -> pd.DataFrame:
    """构造日频变盘指数，只使用时点t及以前的信息。"""

    # 计算各主题过去一段时间的累计收益率。
    returns = theme_prices.pct_change(
        rank_return_window,
        fill_method=None,
    )

    # 每日进行横截面排名，收益率越高，排名越靠前。
    ranks = returns.rank(
        axis=1,
        ascending=False,
        method="average",
    )

    # 当前排名与若干交易日前的排名比较。
    rank_change = ranks - ranks.shift(rank_change_lag)

    # 使用行业总数对排名变化进行标准化。
    industry_count = len(theme_prices.columns)
    rank_std = rank_change.abs().div(industry_count)

    # 计算所有行业标准化排名变化的横截面均值。
    cross_section = rank_std.mean(axis=1, skipna=True)

    # 完整rank_vol_window窗口的滚动标准差。
    volatility = cross_section.rolling(
        window=rank_vol_window,
        min_periods=rank_vol_window,
    ).std()

    # 完整smooth_window窗口的移动平均。
    smooth = volatility.rolling(
        window=smooth_window,
        min_periods=smooth_window,
    ).mean()

    # 变盘指数下降时使用动量，上升时使用反转。
    change = smooth.diff()
    direction = change.apply(
        lambda value: (
            "动量"
            if value < 0
            else ("反转" if value > 0 else None)
        )
    )

    return pd.DataFrame(
        {
            "rank_instability": cross_section,
            "turning_index": smooth,
            "direction": direction,
        }
    )