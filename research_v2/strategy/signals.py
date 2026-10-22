from __future__ import annotations

import math

import pandas as pd


def _selected_count(
    eligible_count: int,
    *,
    top_n: int | None,
    top_fraction: float | None,
    min_holdings: int,
) -> int:
    """Return the pre-declared holding count without using return outcomes."""

    if min_holdings < 1:
        raise ValueError("min_holdings 必须至少为 1。")
    if top_fraction is not None:
        if not 0 < top_fraction <= 1:
            raise ValueError("top_fraction 必须在 (0, 1] 区间内。")
        return min(
            eligible_count,
            max(min_holdings, math.ceil(eligible_count * top_fraction)),
        )
    if top_n is None or top_n < 1:
        raise ValueError("未使用 top_fraction 时，top_n 必须至少为 1。")
    return top_n if eligible_count >= top_n else 0


def _admitted_assets(
    admission_mask: pd.DataFrame | None,
    date: pd.Timestamp,
) -> pd.Index | None:
    """Read the latest admission decision available on or before *date*."""

    if admission_mask is None:
        return None
    history = admission_mask.loc[:date]
    if history.empty:
        raise ValueError(
            f"{date.date()} 已具备因子信号，但没有时点可得的动态准入决策。"
        )
    latest = history.iloc[-1].fillna(False).astype(bool)
    return latest.index[latest]


def build_eligible_equal_weight_signals(
    signals: pd.DataFrame,
    themes: list[str] | pd.Index,
) -> pd.DataFrame:
    """Build a fair benchmark from each signal date's exact eligible pool.

    The returned benchmark has the same signal dates and therefore uses the
    same next-trading-day execution boundary. Eligibility is inferred from the
    non-missing score fields already emitted by :func:`generate_signals`.
    """

    benchmark = signals.copy()
    for date, row in benchmark.iterrows():
        eligible = [
            theme
            for theme in themes
            if pd.notna(row.get(f"score_{theme}"))
        ]
        if not eligible:
            raise ValueError(f"{date.date()} 的基准有效池为空。")
        weight = 1.0 / len(eligible)
        benchmark.at[date, "direction"] = "有效池等权"
        benchmark.at[date, "selected_count"] = len(eligible)
        for theme in themes:
            benchmark.at[date, f"weight_{theme}"] = (
                weight if theme in eligible else 0.0
            )
    return benchmark


def generate_signals(
    theme_prices: pd.DataFrame,
    turning_index: pd.DataFrame,
    momentum_window: int = 252,
    reversal_window: int = 63,
    top_n: int | None = 2,
    signal_mode: str = "turning",
    top_fraction: float | None = None,
    min_holdings: int = 1,
    admission_mask: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """生成月末轮动信号。

    纯动量和纯反转模式只依赖各自因子。只有 Legacy V1 的 turning
    模式继续依赖变盘指数，并使用动量与反转的共同有效样本。

    ``top_fraction`` 用于 V2 的动态持仓数量，按当期有效池向上取整；
    ``top_n`` 保留给 Legacy V1 和实验 A 的固定持仓数量。
    """
    if signal_mode not in {"turning", "momentum", "reversal"}:
        raise ValueError("signal_mode 必须是 turning、momentum 或 reversal。")

    mom = theme_prices.pct_change(momentum_window, fill_method=None)
    rev = (
        -theme_prices.pct_change(reversal_window, fill_method=None)
        if signal_mode in {"turning", "reversal"}
        else None
    )

    rows = []
    month_end_dates = (
        theme_prices.groupby(theme_prices.index.to_period("M"))
        .tail(1)
        .index
    )

    for date in month_end_dates:
        current_prices = theme_prices.loc[:date].iloc[-1]
        mom_factor = mom.loc[:date].iloc[-1]
        rev_factor = rev.loc[:date].iloc[-1] if rev is not None else None

        ti = None
        if signal_mode == "turning":
            if date in turning_index.index:
                ti = turning_index.loc[date]
            else:
                history = turning_index.loc[:date]
                ti = history.iloc[-1] if not history.empty else None
            if ti is None or pd.isna(ti.get("direction")):
                continue

        if signal_mode == "momentum":
            direction = "动量"
            factor = mom_factor
        elif signal_mode == "reversal":
            direction = "反转"
            factor = rev_factor
        else:
            direction = ti["direction"]
            if direction == "动量":
                factor = mom_factor
            elif direction == "反转":
                factor = rev_factor
            else:
                continue

        eligible = current_prices.dropna().index.intersection(
            factor.dropna().index
        )
        # Legacy turning comparisons retain the common valid sample. V2 pure
        # momentum is deliberately independent of reversal history.
        if signal_mode == "turning":
            eligible = (
                eligible.intersection(mom_factor.dropna().index)
                .intersection(rev_factor.dropna().index)
            )
        if eligible.empty:
            continue
        admitted = _admitted_assets(admission_mask, date)
        if admitted is not None:
            eligible = eligible.intersection(admitted)
            if eligible.empty:
                raise ValueError(
                    f"{date.date()} 的准入标的均不具备可交易价格与有效因子，"
                    "动态准入形成了实际空池。"
                )

        holding_count = _selected_count(
            len(eligible),
            top_n=top_n,
            top_fraction=top_fraction,
            min_holdings=min_holdings,
        )
        if holding_count == 0:
            continue

        factor = factor.loc[eligible].sort_values(ascending=False)
        selected = factor.head(holding_count)

        row = {
            "date": date,
            "direction": direction,
            "turning_index": (
                ti.get("turning_index") if ti is not None else pd.NA
            ),
            "eligible_count": len(eligible),
            "selected_count": len(selected),
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
