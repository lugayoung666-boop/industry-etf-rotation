import pandas as pd

from data.cache import load_local_etf_daily, prices_to_wide


def _write_cache(cache_dir, symbol, dates):
    frame = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(dates),
            "ts_code": symbol,
            "close": range(10, 10 + len(dates)),
        }
    )
    frame.to_csv(
        cache_dir / f"{symbol.replace('.', '_')}_akshare.csv",
        index=False,
        encoding="utf-8-sig",
    )


def test_local_cache_preserves_each_etf_own_start_date(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    _write_cache(cache_dir, "OLD.SH", ["2020-01-01", "2020-01-02", "2020-01-03"])
    _write_cache(cache_dir, "NEW.SH", ["2020-01-03", "2020-01-04"])

    raw = load_local_etf_daily(
        ["OLD.SH", "NEW.SH"],
        "2020-01-01",
        "2020-01-04",
        cache_dir,
    )
    wide = prices_to_wide(raw)

    assert wide.index.min() == pd.Timestamp("2020-01-01")
    assert pd.notna(wide.loc[pd.Timestamp("2020-01-01"), "OLD.SH"])
    assert pd.isna(wide.loc[pd.Timestamp("2020-01-01"), "NEW.SH"])
    assert pd.notna(wide.loc[pd.Timestamp("2020-01-03"), "NEW.SH"])
