from pathlib import Path

import pandas as pd
import yaml

from data.cache import load_local_etf_daily, prices_to_wide
from strategy.returns import theme_prices
from strategy.turning_index import build_turning_index
from strategy.signals import generate_signals
from backtest.engine import run_backtest
from analysis.performance import calculate_performance


TRAIN_START = "2021-02-04"
TRAIN_END = "2023-12-31"

VALID_START = "2024-01-01"
VALID_END = "2024-12-31"

SIGNAL_MODE = "turning"
TOP_N_VALUES = (1, 2, 3, 4)


def evaluate_period(
    prices,
    signals,
    mapping,
    strategy_config,
    period_name,
    start_date,
    end_date,
    top_n,
):
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    period_prices = prices.loc[
        (prices.index >= start) & (prices.index <= end)
    ]

    # 保留区间开始前最后一个月末信号，
    # 使其能在区间首个交易日执行。
    previous_signal = signals.loc[signals.index < start].tail(1)
    current_signals = signals.loc[
        (signals.index >= start) & (signals.index <= end)
    ]

    period_signals = (
        pd.concat([previous_signal, current_signals])
        .sort_index()
        .loc[lambda frame: ~frame.index.duplicated(keep="last")]
    )

    if period_prices.empty:
        raise ValueError(f"{period_name}没有可用行情数据。")

    if period_signals.empty:
        raise ValueError(f"{period_name}没有可用交易信号。")

    result, trades = run_backtest(
        period_prices,
        period_signals,
        mapping,
        strategy_config["initial_cash"],
        strategy_config["fee"],
        strategy_config["slippage"],
    )

    performance = calculate_performance(
    result,
    trades,
    strategy_config["initial_cash"],
).iloc[0]

    return {
        "period": period_name,
        "start_date": start_date,
        "end_date": end_date,
        "signal_mode": SIGNAL_MODE,
        "top_n": top_n,
        "cumulative_return": performance.iloc[0],
        "annual_return": performance.iloc[1],
        "max_drawdown": performance.iloc[4],
        "sharpe": performance.iloc[3],
        "trades": performance.iloc[7],
        "avg_turnover": performance.iloc[8],
    }


def main():
    root = Path(__file__).parent

    universe_config = yaml.safe_load(
        (root / "config/universe.yaml").read_text(encoding="utf-8")
    )
    strategy_config = yaml.safe_load(
        (root / "config/strategy.yaml").read_text(encoding="utf-8")
    )

    if strategy_config.get("signal_mode") != SIGNAL_MODE:
        raise ValueError(
            "optimize_oos.py 只允许优化 turning 主策略。"
            "请将 strategy.yaml 中的 signal_mode 改为 turning。"
        )

    mapping = {
        theme: codes[0]
        for theme, codes in universe_config["themes"].items()
    }

    # 只加载到验证期结束，禁止优化阶段读取最终测试数据。
    raw = load_local_etf_daily(
        list(mapping.values()),
        strategy_config["start_date"],
        VALID_END,
        root / "data/cache",
    )

    prices = prices_to_wide(raw)
    themes = theme_prices(prices, mapping)

    turning = build_turning_index(
        themes,
        strategy_config["rank_return_window"],
        strategy_config["rank_change_lag"],
        strategy_config["rank_vol_window"],
        strategy_config["rank_smooth_window"],
    )

    rows = []

    for top_n in TOP_N_VALUES:
        signals = generate_signals(
            themes,
            turning,
            strategy_config["momentum_window"],
            strategy_config["reversal_window"],
            top_n,
            SIGNAL_MODE,
        )

        rows.append(
            evaluate_period(
                prices,
                signals,
                mapping,
                strategy_config,
                "train",
                TRAIN_START,
                TRAIN_END,
                top_n,
            )
        )

        rows.append(
            evaluate_period(
                prices,
                signals,
                mapping,
                strategy_config,
                "validation",
                VALID_START,
                VALID_END,
                top_n,
            )
        )

    results = pd.DataFrame(rows)

    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_dir
        / "optimization_turning_train_validation.csv"
    )
    results.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        results.sort_values(
            ["period", "sharpe"],
            ascending=[True, False],
        ).to_string(index=False)
    )

    print(f"\n结果已保存至: {output_path}")
    print("注意：本脚本没有读取或计算2025—2026最终测试期。")


if __name__ == "__main__":
    main()
