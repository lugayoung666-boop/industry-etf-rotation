import pandas as pd


def validate_prices(prices: pd.DataFrame) -> None:
    if prices.empty or not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("价格数据为空或索引不是 DatetimeIndex。")
    if (prices <= 0).any().any():
        raise ValueError("价格中存在非正数。")
    if not prices.index.is_monotonic_increasing or prices.index.has_duplicates:
        raise ValueError("价格日期必须升序且不可重复。")
