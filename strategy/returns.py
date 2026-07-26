import pandas as pd


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.sort_index().pct_change()


def theme_prices(prices: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    out = {}
    for theme, code in mapping.items():
        if code in prices:
            out[theme] = prices[code]
    return pd.DataFrame(out, index=prices.index)
