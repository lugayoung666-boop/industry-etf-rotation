import csv

import pytest

from research_v2.analysis.momentum_validity_gate import (
    evaluate_momentum,
    gate_summary,
    load_momentum_rows,
)


def _row(source: str, *, ic: float = 0.06, ic_p: float = 0.02,
         spread: float = 0.01, spread_p: float = 0.03) -> dict[str, str]:
    return {
        "source": source,
        "factor": "momentum",
        "periods": "100",
        "mean_rank_ic": str(ic),
        "rank_ic_p_value_two_sided": str(ic_p),
        "mean_top_minus_bottom": str(spread),
        "top_minus_bottom_p_value_two_sided": str(spread_p),
        "aggregate_group_monotonicity": "0.8",
        "positive_year_rate": "0.7",
    }


def test_dual_gate_requires_both_rank_ic_and_spread() -> None:
    rows = [_row("a", spread_p=0.20)]

    result = evaluate_momentum(rows, sources=["a"])[0]

    assert result["rank_ic_passed"] is True
    assert result["spread_passed"] is False
    assert result["primary_validity_passed"] is False


def test_gate_summary_does_not_promote_mixed_evidence() -> None:
    results = [
        {"primary_validity_passed": True},
        {"primary_validity_passed": False},
    ]

    summary = gate_summary(results)

    assert summary["status"] == "MIXED_RUNTIME_EVIDENCE"
    assert summary["promotion_allowed"] is False


def test_evaluation_rejects_missing_or_duplicate_sources() -> None:
    with pytest.raises(ValueError, match="实际为 0 行"):
        evaluate_momentum([_row("a")], sources=["b"])
    with pytest.raises(ValueError, match="实际为 2 行"):
        evaluate_momentum([_row("a"), _row("a")], sources=["a"])


def test_loader_keeps_only_momentum(tmp_path) -> None:
    path = tmp_path / "summary.csv"
    fields = list(_row("a"))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(_row("a"))
        reversal = _row("b")
        reversal["factor"] = "reversal"
        writer.writerow(reversal)

    assert load_momentum_rows(path) == [_row("a")]
