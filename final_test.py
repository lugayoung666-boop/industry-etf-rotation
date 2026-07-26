from pathlib import Path

import pandas as pd
import yaml

from data.cache import load_local_etf_daily, prices_to_wide
from strategy.returns import theme_prices
from strategy.turning_index import build_turning_index
from strategy.signals import generate_signals
from optimize_oos import evaluate_period


TEST_START = "2025-01-01"
TEST_END = "2026-07-14"

FINAL_SIGNAL_MODE = "turning"
FINAL_TOP_N = 3


def main():
    root = Path(__file__).parent

    universe_config = yaml.safe_load(
        (root / "config/universe.yaml").read_text(encoding="utf-8")
    )
    strategy_config = yaml.safe_load(
        (root / "config/strategy.yaml").read_text(encoding="utf-8")
    )

    if strategy_config.get("signal_mode") != FINAL_SIGNAL_MODE:
        raise ValueError(
            "最终测试只允许使用 turning 主策略。"
        )

    if strategy_config.get("top_n") != FINAL_TOP_N:
        raise ValueError(
            "最终测试参数已冻结为 top_n=3，"
            "请将 strategy.yaml 中的 top_n 改为3。"
        )

    mapping = {
        theme: codes[0]
        for theme, codes in universe_config["themes"].items()
    }

    # 加载测试期之前的历史数据，用于形成滚动指标。
    raw = load_local_etf_daily(
        list(mapping.values()),
        strategy_config["start_date"],
        TEST_END,
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

    signals = generate_signals(
        themes,
        turning,
        strategy_config["momentum_window"],
        strategy_config["reversal_window"],
        FINAL_TOP_N,
        FINAL_SIGNAL_MODE,
    )

    result = evaluate_period(
        prices,
        signals,
        mapping,
        strategy_config,
        "final_test",
        TEST_START,
        TEST_END,
        FINAL_TOP_N,
    )

    output = pd.DataFrame([result])

    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "final_test_turning_top3.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(output.to_string(index=False))
    print(f"\n最终测试结果已保存至: {output_path}")


if __name__ == "__main__":
    main()
