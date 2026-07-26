from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import yaml

from data.cache import prices_to_wide, load_local_etf_daily
from data.tushare_client import download_etf_daily as download_tushare
from data.akshare_client import download_etf_daily as download_akshare
from data.validators import validate_prices
from strategy.returns import theme_prices
from strategy.turning_index import build_turning_index
from strategy.signals import generate_signals
from backtest.engine import run_backtest
from analysis.performance import calculate_performance, equal_weight_benchmark
from analysis.reports import write_report


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--download", action="store_true", help="先通过 AkShare 下载/刷新本地缓存"); ap.add_argument("--source", choices=["local", "akshare", "tushare"], default="local"); ap.add_argument("--output", default="output"); args=ap.parse_args()
    root=Path(__file__).parent; cfg=yaml.safe_load((root/"config/universe.yaml").read_text(encoding="utf-8")); st=yaml.safe_load((root/"config/strategy.yaml").read_text(encoding="utf-8"))
    mapping={theme: codes[0] for theme,codes in cfg["themes"].items()}; codes=list(mapping.values())
    if args.download:
        raw=download_akshare(codes, st["start_date"], st["end_date"], root/"data/cache")
        prices=prices_to_wide(raw, "close")
    elif args.source == "local":
        raw=load_local_etf_daily(codes, st["start_date"], st["end_date"], root/"data/cache")
        prices=prices_to_wide(raw, "close")
    else:
        downloader = download_akshare if args.source == "akshare" else download_tushare
        raw=downloader(codes, st["start_date"], st["end_date"], root/"data/cache")
        prices=prices_to_wide(raw, "close")
    available_codes = [code for code in codes if code in prices.columns and prices[code].notna().any()]
    if len(available_codes) < 2:
        raise ValueError(f"可用 ETF 少于 2 只，当前仅有: {available_codes}")
    prices=prices[available_codes].dropna(axis=1, how="all")
    mapping = {k: v for k, v in mapping.items() if v in prices.columns}
    validate_prices(prices)
    themes=theme_prices(prices, mapping).dropna(how="all")
    turning=build_turning_index(themes, st["rank_return_window"], st["rank_change_lag"], st["rank_vol_window"], st["rank_smooth_window"])
    signals=generate_signals(themes, turning, st["momentum_window"], st["reversal_window"], st["top_n"], st.get("signal_mode", "turning"))
    result,trades=run_backtest(prices, signals, mapping, st["initial_cash"], st["fee"], st["slippage"])
    perf = calculate_performance(
    result,
    trades,
    st["initial_cash"],
)
    outdir = root / args.output
    outdir.mkdir(parents=True, exist_ok=True)
    benchmark = equal_weight_benchmark(prices, st["initial_cash"])
    benchmark.to_csv(outdir / "equal_weight_benchmark.csv", encoding="utf-8-sig")
    write_report(outdir,result,trades,perf,turning,signals)
    cache_files = sorted((root / "data/cache").glob("*_akshare.csv"))
    metadata = {
        "data_source": "akshare_download" if args.download or args.source == "akshare" else "local_akshare_cache",
        "synthetic_data_used": False,
        "cache_files": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in cache_files],
        "price_start": str(prices.index.min().date()), "price_end": str(prices.index.max().date()),
        "theme_count": len(mapping), "signal_mode": st.get("signal_mode", "turning"),
        "top_n": st["top_n"], "fee": st["fee"], "slippage": st["slippage"]
    }
    (outdir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    output_path = (root / args.output).resolve()
    print(perf.to_string(index=False)); print(f"输出目录: {output_path}")

if __name__ == "__main__": main()
