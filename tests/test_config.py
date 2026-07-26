from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def test_report_params_match_runtime_rank_change_lag():
    runtime = yaml.safe_load((ROOT / "config" / "strategy.yaml").read_text(encoding="utf-8"))
    report = yaml.safe_load(
        (ROOT / "config" / "strategy_report_params.yaml").read_text(encoding="utf-8")
    )

    assert report["rank_change_lag"] == runtime["rank_change_lag"]
