from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pandas as pd


def _api(token: str | None = None):
    import tushare as ts

    token = token or os.getenv("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("未找到 TUSHARE_TOKEN，请先设置环境变量。")
    ts.set_token(token)
    return ts.pro_api()


def download_etf_daily(symbols: Iterable[str], start_date: str, end_date: str,
                       cache_dir: str | Path = "data/cache", token: str | None = None) -> pd.DataFrame:
    """Download ETF daily data. Cache is used first and refreshed only when missing."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    api = _api(token)
    frames = []
    for symbol in symbols:
        path = cache / f"{symbol.replace('.', '_')}.csv"
        if path.exists():
            frame = pd.read_csv(path, parse_dates=["trade_date"])
            if frame["trade_date"].min() > pd.Timestamp(start_date) or frame["trade_date"].max() < pd.Timestamp(end_date):
                frame = api.fund_daily(ts_code=symbol, start_date=start_date.replace("-", ""),
                                       end_date=end_date.replace("-", ""))
                if frame.empty:
                    raise ValueError(f"Tushare 未返回 {symbol} 的基金日线数据。")
                frame["trade_date"] = pd.to_datetime(frame["trade_date"])
                frame.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            frame = api.fund_daily(ts_code=symbol, start_date=start_date.replace("-", ""),
                                   end_date=end_date.replace("-", ""))
            if frame.empty:
                raise ValueError(f"Tushare 未返回 {symbol} 的基金日线数据。")
            frame["trade_date"] = pd.to_datetime(frame["trade_date"])
            frame.to_csv(path, index=False, encoding="utf-8-sig")
        frame = frame[(frame.trade_date >= start_date) & (frame.trade_date <= end_date)].copy()
        frame["ts_code"] = symbol
        frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["trade_date", "ts_code"]).drop_duplicates(["trade_date", "ts_code"])
    return out
