from __future__ import annotations
import pandas as pd


def run_backtest(prices: pd.DataFrame, signals: pd.DataFrame, theme_to_code: dict[str, str],
                 initial_cash: float = 1_000_000, fee: float = .0005,
                 slippage: float = .0005) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = prices.sort_index().ffill()
    codes = list(theme_to_code.values())
    value, cash, holdings, previous_weights = initial_cash, initial_cash, {}, {}
    daily, trades = [], []
    signal_by_date = {}
    for signal_date, signal in signals.to_dict("index").items():
        pos = prices.index.searchsorted(signal_date, side="right")
        if pos < len(prices.index):
            signal_by_date[prices.index[pos]] = signal
    for date, row in prices[codes].iterrows():
        if holdings:
            value = cash + sum(qty * row[code] for code, qty in holdings.items())
        if date in signal_by_date:
            s = signal_by_date[date]
            target = {theme_to_code[t]: s.get(f"weight_{t}", 0) for t in theme_to_code}
            turnover = sum(abs(target.get(c, 0) - previous_weights.get(c, 0)) for c in codes)
            cost = value * turnover * (fee + slippage)
            cash = value - cost
            holdings = {c: (cash * w) / row[c] for c, w in target.items() if w > 0 and pd.notna(row[c])}
            cash = cash * (1 - sum(target.values()))
            value = cash + sum(qty * row[c] for c, qty in holdings.items())
            previous_weights = target
            trades.append({"date": date, "direction": s["direction"], "turnover": turnover,
                           "cost": cost, "portfolio_value": value, **target})
        daily.append({"date": date, "portfolio_value": value, "cash": cash,
                      "invested": value - cash})
    result = pd.DataFrame(daily).set_index("date")
    result["return"] = result.portfolio_value.pct_change().fillna(0)
    result["drawdown"] = result.portfolio_value / result.portfolio_value.cummax() - 1
    return result, pd.DataFrame(trades)
