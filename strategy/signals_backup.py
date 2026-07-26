import pandas as pd


def generate_signals(theme_prices: pd.DataFrame, turning_index: pd.DataFrame,
                     momentum_window: int = 252, reversal_window: int = 63,
                     top_n: int = 2, signal_mode: str = "turning") -> pd.DataFrame:
    mom = theme_prices.pct_change(momentum_window, fill_method=None)
    rev = -theme_prices.pct_change(reversal_window, fill_method=None)
    rows = []
    month_end_dates = theme_prices.groupby(theme_prices.index.to_period("M")).tail(1).index
    for date in month_end_dates:
        available = theme_prices.loc[:date].iloc[-1]
        if date not in turning_index.index:
            ti = turning_index.loc[:date].iloc[-1] if not turning_index.loc[:date].empty else None
        else:
            ti = turning_index.loc[date]
        if ti is None or pd.isna(ti.get("direction")):
            continue
        if signal_mode == "momentum":
            direction, factor = "动量", mom.loc[:date].iloc[-1]
        elif signal_mode == "reversal":
            direction, factor = "反转", rev.loc[:date].iloc[-1]
        elif signal_mode == "turning":
            direction = ti["direction"]
            factor = mom.loc[:date].iloc[-1] if direction == "动量" else rev.loc[:date].iloc[-1]
        else:
            raise ValueError("signal_mode 必须是 turning、momentum 或 reversal。")
        factor = factor.dropna().sort_values(ascending=False).head(top_n)
        row = {"date": date, "direction": direction, "turning_index": ti["turning_index"]}
        for theme in theme_prices.columns:
            row[f"weight_{theme}"] = 1.0 / len(factor) if theme in factor.index else 0.0
            row[f"score_{theme}"] = factor.get(theme)
        rows.append(row)
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()
