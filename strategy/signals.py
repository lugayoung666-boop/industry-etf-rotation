import pandas as pd


def generate_signals(
    theme_prices: pd.DataFrame,
    turning_index: pd.DataFrame,
    momentum_window: int = 252,
    reversal_window: int = 63,
    top_n: int = 2,
    signal_mode: str = "turning",
) -> pd.DataFrame:
    """生成月末轮动信号。

    为保证动量、反转和变盘指数使用相同的可比样本，
    只有在两类因子均有足够历史数据时才开始生成信号。
    """
    mom = theme_prices.pct_change(momentum_window, fill_method=None)
    rev = -theme_prices.pct_change(reversal_window, fill_method=None)

    rows = []
    month_end_dates = (
        theme_prices.groupby(theme_prices.index.to_period("M"))
        .tail(1)
        .index
    )

    for date in month_end_dates:
        if date in turning_index.index:
            ti = turning_index.loc[date]
        else:
            history = turning_index.loc[:date]
            ti = history.iloc[-1] if not history.empty else None

        if ti is None or pd.isna(ti.get("direction")):
            continue

        current_prices = theme_prices.loc[:date].iloc[-1]
        mom_factor = mom.loc[:date].iloc[-1]
        rev_factor = rev.loc[:date].iloc[-1]

        # 使用共同有效样本，避免某种因子尚未形成时被当成空仓信号。
        eligible = (
            current_prices.dropna().index
            .intersection(mom_factor.dropna().index)
            .intersection(rev_factor.dropna().index)
        )

        if len(eligible) < top_n:
            continue

        if signal_mode == "momentum":
            direction = "动量"
            factor = mom_factor.loc[eligible]
        elif signal_mode == "reversal":
            direction = "反转"
            factor = rev_factor.loc[eligible]
        elif signal_mode == "turning":
            direction = ti["direction"]
            if direction == "动量":
                factor = mom_factor.loc[eligible]
            elif direction == "反转":
                factor = rev_factor.loc[eligible]
            else:
                continue
        else:
            raise ValueError(
                "signal_mode 必须是 turning、momentum 或 reversal。"
            )

        factor = factor.sort_values(ascending=False)
        selected = factor.head(top_n)

        row = {
            "date": date,
            "direction": direction,
            "turning_index": ti["turning_index"],
        }

        for theme in theme_prices.columns:
            row[f"weight_{theme}"] = (
                1.0 / len(selected) if theme in selected.index else 0.0
            )
            # 保存所有有效标的得分，而不只是入选标的。
            row[f"score_{theme}"] = factor.get(theme)

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).set_index("date")
