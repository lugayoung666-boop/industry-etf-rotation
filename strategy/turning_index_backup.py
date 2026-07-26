import pandas as pd


def build_turning_index(theme_prices: pd.DataFrame, rank_return_window: int = 21,
                        rank_change_lag: int = 21, rank_vol_window: int = 220,
                        smooth_window: int = 20) -> pd.DataFrame:
    """Build daily rank-instability index, using only information available at date t."""
    returns = theme_prices.pct_change(rank_return_window, fill_method=None)
    ranks = returns.rank(axis=1, ascending=False, method="average")
    rank_change = ranks - ranks.shift(rank_change_lag)
    rank_std = rank_change.abs().div(len(theme_prices.columns))
    cross_section = rank_std.mean(axis=1, skipna=True)
    volatility = cross_section.rolling(rank_vol_window, min_periods=max(20, rank_vol_window // 4)).std()
    smooth = volatility.rolling(smooth_window, min_periods=max(5, smooth_window // 2)).mean()
    direction = smooth.diff().apply(lambda x: "动量" if x < 0 else ("反转" if x > 0 else None))
    return pd.DataFrame({"rank_instability": cross_section, "turning_index": smooth,
                         "direction": direction})
