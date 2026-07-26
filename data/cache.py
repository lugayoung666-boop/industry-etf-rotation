from pathlib import Path
import pandas as pd


def load_csv_prices(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["trade_date"])
    required = {"trade_date", "ts_code", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV 缺少字段: {sorted(missing)}")
    df = df.sort_values(["trade_date", "ts_code"]).drop_duplicates(["trade_date", "ts_code"])
    return df


def prices_to_wide(df: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
    return df.pivot(index="trade_date", columns="ts_code", values=price_col).sort_index()


def load_local_etf_daily(symbols, start_date: str, end_date: str,
                         cache_dir: str | Path = "data/cache") -> pd.DataFrame:
    """Read the previously downloaded AkShare cache without any network call."""
    cache = Path(cache_dir)
    frames = []
    min_dates, max_dates = [], []
    for symbol in symbols:
        path = cache / f"{symbol.replace('.', '_')}_akshare.csv"
        if not path.exists():
            raise FileNotFoundError(f"本地行情不存在: {path}，请先运行 --download。")
        frame = pd.read_csv(path, parse_dates=["trade_date"])
        min_dates.append(frame["trade_date"].min())
        max_dates.append(frame["trade_date"].max())
        frames.append(frame)
    effective_start = max(pd.Timestamp(start_date), max(min_dates))
    effective_end = min(pd.Timestamp(end_date), min(max_dates))
    if effective_start >= effective_end:
        raise ValueError("本地 ETF 缓存没有共同的有效日期区间，请先运行 --download 刷新。")
    frames = [frame[(frame.trade_date >= effective_start) & (frame.trade_date <= effective_end)] for frame in frames]
    return pd.concat(frames, ignore_index=True).sort_values(["trade_date", "ts_code"])
