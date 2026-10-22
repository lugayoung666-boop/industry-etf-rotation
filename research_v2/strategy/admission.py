from __future__ import annotations

from pathlib import Path

import pandas as pd


_TRUE_VALUES = {"true", "1", "yes", "y"}
_FALSE_VALUES = {"false", "0", "no", "n"}


def _parse_decision(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in {0, 1}:
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"无法识别的动态准入值: {value!r}")


def load_admission_mask(
    path: str | Path,
    expected_assets: list[str],
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Load a pre-registered, point-in-time monthly admission decision table."""

    path = Path(path)
    frame = pd.read_csv(path)
    if "date" not in frame:
        raise ValueError("动态准入文件必须包含 date 列。")
    missing = set(expected_assets) - set(frame.columns)
    unexpected = set(frame.columns) - {"date", *expected_assets}
    if missing:
        raise ValueError(f"动态准入文件缺少标的列: {sorted(missing)}")
    if unexpected:
        raise ValueError(f"动态准入文件包含未知列: {sorted(unexpected)}")

    dates = pd.to_datetime(frame.pop("date"), errors="coerce")
    if dates.isna().any():
        raise ValueError("动态准入文件包含无法解析的 date。")
    if dates.duplicated().any():
        duplicates = dates[dates.duplicated()].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"动态准入文件包含重复日期: {duplicates}")

    mask = frame[expected_assets].map(_parse_decision)
    mask.index = dates
    mask = mask.sort_index()
    if start_date is not None:
        mask = mask.loc[mask.index >= pd.Timestamp(start_date)]
    if end_date is not None:
        mask = mask.loc[mask.index <= pd.Timestamp(end_date)]
    if mask.empty:
        raise ValueError("动态准入文件在策略区间内没有决策记录。")
    if mask.sum(axis=1).eq(0).any():
        dates = mask.index[mask.sum(axis=1).eq(0)].strftime("%Y-%m-%d").tolist()
        raise ValueError(f"动态准入决策不得形成空池: {dates}")
    return mask


def admission_audit(mask: pd.DataFrame) -> pd.DataFrame:
    """Return a stable long-form audit table for every admission decision."""

    audit = (
        mask.rename_axis("date")
        .reset_index()
        .melt(id_vars="date", var_name="asset", value_name="admitted")
        .sort_values(["date", "asset"])
        .reset_index(drop=True)
    )
    audit["admitted"] = audit["admitted"].astype(bool)
    return audit


def admission_coverage_audit(
    mask: pd.DataFrame,
    signal_dates: pd.Index | list[pd.Timestamp],
) -> pd.DataFrame:
    """Map each strategy signal date to the point-in-time decision it used."""

    rows = []
    for signal_date in pd.DatetimeIndex(signal_dates).sort_values().unique():
        history = mask.loc[:signal_date]
        if history.empty:
            rows.append(
                {
                    "signal_date": signal_date,
                    "decision_date": pd.NaT,
                    "decision_age_days": pd.NA,
                    "admitted_count": 0,
                    "covered": False,
                }
            )
            continue
        decision_date = history.index[-1]
        rows.append(
            {
                "signal_date": signal_date,
                "decision_date": decision_date,
                "decision_age_days": int((signal_date - decision_date).days),
                "admitted_count": int(history.iloc[-1].sum()),
                "covered": True,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "signal_date",
            "decision_date",
            "decision_age_days",
            "admitted_count",
            "covered",
        ],
    )


def summarize_admission(mask: pd.DataFrame) -> dict:
    counts = mask.sum(axis=1)
    return {
        "decision_rows": int(len(mask)),
        "asset_count": int(mask.shape[1]),
        "decision_start": str(mask.index.min().date()),
        "decision_end": str(mask.index.max().date()),
        "admitted_count_min": int(counts.min()),
        "admitted_count_max": int(counts.max()),
        "admitted_count_mean": float(counts.mean()),
    }
