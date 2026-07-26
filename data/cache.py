from pathlib import Path

import pandas as pd


def load_csv_prices(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["trade_date"])
    required = {"trade_date", "ts_code", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing fields: {sorted(missing)}")
    df = df.sort_values(["trade_date", "ts_code"]).drop_duplicates(
        ["trade_date", "ts_code"]
    )
    return df


def prices_to_wide(df: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
    return df.pivot(index="trade_date", columns="ts_code", values=price_col).sort_index()


def load_local_etf_daily(
    symbols,
    start_date: str,
    end_date: str,
    cache_dir: str | Path = "data/cache",
) -> pd.DataFrame:
    """Read local AkShare cache without forcing all ETFs onto one start date.

    V2 keeps each ETF on its own available date range. Newly listed ETFs should
    appear as missing values before their listing date after pivoting, instead of
    pushing the entire backtest sample to the latest common listing date.
    """
    cache = Path(cache_dir)
    frames = []
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    for symbol in symbols:
        path = cache / f"{symbol.replace('.', '_')}_akshare.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Local ETF cache not found: {path}. Run with --download first."
            )

        frame = pd.read_csv(path, parse_dates=["trade_date"])
        required = {"trade_date", "close"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"ETF cache {path} missing fields: {sorted(missing)}")

        if "ts_code" not in frame.columns:
            frame["ts_code"] = symbol
        frame = frame[["trade_date", "ts_code", "close"]].copy()
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame = frame.dropna(subset=["trade_date", "ts_code", "close"])
        frame = frame[(frame.trade_date >= start) & (frame.trade_date <= end)]
        if not frame.empty:
            frames.append(frame)

    if not frames:
        raise ValueError("No local ETF cache rows overlap the requested date range.")

    return pd.concat(frames, ignore_index=True).sort_values(["trade_date", "ts_code"])
