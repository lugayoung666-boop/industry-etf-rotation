from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def _symbol(code: str) -> str:
    return code.split(".", 1)[0]


def _normalize(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame.empty:
        raise ValueError(f"AkShare 未返回 ETF {symbol} 的行情数据。")
    frame = frame.rename(columns={"日期": "trade_date", "date": "trade_date",
                                  "收盘": "close", "close": "close"})
    required = {"trade_date", "close"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"AkShare ETF {symbol} 缺少字段: {sorted(missing)}")
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame["ts_code"] = symbol
    out = frame[["trade_date", "ts_code", "close"]].dropna().sort_values("trade_date")
    return _adjust_discontinuities(out)


def _adjust_discontinuities(out: pd.DataFrame) -> pd.DataFrame:
    out = out.copy()
    # Sina's ETF history is unadjusted. Correct obvious split/reverse-split jumps
    # so the fallback does not create fictitious multi-day losses or gains.
    out["raw_return"] = out["close"].pct_change()
    for index in out.index[out["raw_return"].abs() > 0.30]:
        ratio = out.at[index, "close"] / out["close"].shift(1).at[index]
        out.loc[out.index < index, "close"] *= ratio
    return out.drop(columns="raw_return")


def download_etf_daily(symbols: Iterable[str], start_date: str, end_date: str,
                       cache_dir: str | Path = "data/cache") -> pd.DataFrame:
    """Fetch ETF daily close from AkShare and cache normalized CSV files."""
    import akshare as ak

    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    frames = []
    for symbol in symbols:
        path = cache / f"{symbol.replace('.', '_')}_akshare.csv"
        if path.exists():
            frame = pd.read_csv(path, parse_dates=["trade_date"])
            frame = _adjust_discontinuities(frame)
            if frame["trade_date"].min() > pd.Timestamp(start_date) or frame["trade_date"].max() < pd.Timestamp(end_date):
                frame = None
        else:
            frame = None
        if frame is None:
            try:
                raw = ak.fund_etf_hist_em(symbol=_symbol(symbol), period="daily",
                                          start_date=start_date.replace("-", ""),
                                          end_date=end_date.replace("-", ""), adjust="qfq")
            except Exception as em_error:
                try:
                    raw = ak.fund_etf_hist_sina(symbol=("sh" if symbol.endswith(".SH") else "sz") + _symbol(symbol))
                except Exception as sina_error:
                    raise RuntimeError(f"AkShare 获取 {symbol} 失败：东方财富和新浪接口均不可用。") from sina_error
            frame = _normalize(raw, symbol)
            frame.to_csv(path, index=False, encoding="utf-8-sig")
        frame = frame[(frame.trade_date >= start_date) & (frame.trade_date <= end_date)].copy()
        frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["trade_date", "ts_code"]).drop_duplicates(["trade_date", "ts_code"])
