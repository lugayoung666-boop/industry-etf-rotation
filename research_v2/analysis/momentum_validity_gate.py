from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


SOURCE_LABELS = {
    "citic_l1_industries_runtime": "中信一级行业／252日",
    "citic_l2_industries_runtime": "中信二级行业／252日",
    "legacy_etf_6_runtime": "6 ETF／252日",
    "full_etf_16_runtime": "16 ETF／252日",
    "citic_l1_industries_report": "中信一级行业／240日",
    "citic_l2_industries_report": "中信二级行业／240日",
    "legacy_etf_6_report": "6 ETF／240日",
    "full_etf_16_report": "16 ETF／240日",
}

RUNTIME_SOURCES = tuple(
    source for source in SOURCE_LABELS if source.endswith("_runtime")
)
REPORT_SOURCES = tuple(
    source for source in SOURCE_LABELS if source.endswith("_report")
)


def _as_float(row: dict[str, str], field: str) -> float:
    try:
        return float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"字段 {field} 不是有效数值: {row.get(field)!r}") from exc


def load_momentum_rows(path: str | Path) -> list[dict[str, str]]:
    """Load the pre-computed factor table and retain pure momentum only."""

    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("factor") == "momentum"
        ]
    if not rows:
        raise ValueError("因子汇总表中没有 momentum 行。")
    return rows


def evaluate_momentum(
    rows: Iterable[dict[str, str]],
    *,
    sources: Iterable[str],
    alpha: float = 0.05,
) -> list[dict[str, object]]:
    """Evaluate the pre-registered dual evidence rule for each cross-section.

    A source passes only when both mean RankIC and mean Top-Bottom spread are
    positive and their two-sided p-values are below ``alpha``.  The function
    deliberately recomputes the gate from numeric fields instead of trusting
    the verdict text stored in an earlier report.
    """

    if not 0 < alpha < 1:
        raise ValueError("alpha 必须位于 (0, 1) 区间。")

    by_source: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_source.setdefault(row.get("source", ""), []).append(row)

    results: list[dict[str, object]] = []
    for source in sources:
        matches = by_source.get(source, [])
        if len(matches) != 1:
            raise ValueError(
                f"{source} 应有且仅有一行纯动量统计，实际为 {len(matches)} 行。"
            )
        row = matches[0]
        rank_ic = _as_float(row, "mean_rank_ic")
        rank_p = _as_float(row, "rank_ic_p_value_two_sided")
        spread = _as_float(row, "mean_top_minus_bottom")
        spread_p = _as_float(row, "top_minus_bottom_p_value_two_sided")
        monotonicity = _as_float(row, "aggregate_group_monotonicity")
        positive_year_rate = _as_float(row, "positive_year_rate")
        rank_pass = rank_ic > 0 and rank_p < alpha
        spread_pass = spread > 0 and spread_p < alpha
        results.append(
            {
                "source": source,
                "label": SOURCE_LABELS.get(source, source),
                "periods": int(float(row["periods"])),
                "mean_rank_ic": rank_ic,
                "rank_ic_p_value_two_sided": rank_p,
                "mean_top_minus_bottom": spread,
                "top_minus_bottom_p_value_two_sided": spread_p,
                "aggregate_group_monotonicity": monotonicity,
                "positive_year_rate": positive_year_rate,
                "rank_ic_passed": rank_pass,
                "spread_passed": spread_pass,
                "primary_validity_passed": rank_pass and spread_pass,
            }
        )
    return results


def gate_summary(runtime_results: Iterable[dict[str, object]]) -> dict[str, object]:
    results = list(runtime_results)
    if not results:
        raise ValueError("运行口径结果为空。")
    passed = sum(bool(row["primary_validity_passed"]) for row in results)
    if passed == len(results):
        status = "VALIDATED_ACROSS_ALL_RUNTIME_CROSS_SECTIONS"
    elif passed:
        status = "MIXED_RUNTIME_EVIDENCE"
    else:
        status = "NOT_VALIDATED"
    return {
        "status": status,
        "runtime_source_count": len(results),
        "runtime_passed_source_count": passed,
        "promotion_allowed": status
        == "VALIDATED_ACROSS_ALL_RUNTIME_CROSS_SECTIONS",
        "interpretation": (
            "当前纯动量尚未通过统一有效性闸门；A/B/C 只能作为探索性策略实验，"
            "不得把回测收益解释为已验证的因子收益。"
            if status != "VALIDATED_ACROSS_ALL_RUNTIME_CROSS_SECTIONS"
            else "纯动量已在全部运行口径横截面通过预设双重统计门槛。"
        ),
    }


def write_outputs(
    output_dir: str | Path,
    runtime_results: list[dict[str, object]],
    report_results: list[dict[str, object]],
    *,
    input_path: str | Path,
    alpha: float,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_results = runtime_results + report_results
    fields = list(all_results[0])
    with (output_dir / "momentum_validity_summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_results)

    gate = gate_summary(runtime_results)
    payload = {
        **gate,
        "alpha": alpha,
        "primary_specification": "252_trading_day_momentum",
        "robustness_specification": "240_trading_day_momentum",
        "input_file": str(Path(input_path)),
    }
    (output_dir / "momentum_validity_gate.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    def table(rows: list[dict[str, object]]) -> list[str]:
        lines = [
            "| 横截面 | 期数 | RankIC | p值 | Top−Bottom | p值 | 分组单调性 | 正年份占比 | 通过 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
        ]
        for row in rows:
            lines.append(
                "| {label} | {periods} | {ic:.4f} | {icp:.4f} | {spread:.2%} | "
                "{spreadp:.4f} | {mono:.2f} | {years:.1%} | {passed} |".format(
                    label=row["label"],
                    periods=row["periods"],
                    ic=row["mean_rank_ic"],
                    icp=row["rank_ic_p_value_two_sided"],
                    spread=row["mean_top_minus_bottom"],
                    spreadp=row["top_minus_bottom_p_value_two_sided"],
                    mono=row["aggregate_group_monotonicity"],
                    years=row["positive_year_rate"],
                    passed="是" if row["primary_validity_passed"] else "否",
                )
            )
        return lines

    report = [
        "# 去反转后的纯动量统一有效性验收",
        "",
        "## 验收边界",
        "",
        "- V2 主口径固定为 252 个交易日动量；240 日研报参数只作稳健性诊断，不用于择优。",
        "- 月末形成信号、下一交易日进入、持有至下一期执行边界；不使用组合权重、交易成本或 TopN。",
        f"- 单一横截面只有在 RankIC>0 且双侧 p<{alpha:.2f}，同时 Top−Bottom>0 且双侧 p<{alpha:.2f} 时通过。",
        "",
        "## 主验收：252 日纯动量",
        "",
        *table(runtime_results),
        "",
        f"统一结论：**{gate['status']}**。{gate['interpretation']}",
        "",
        "## 稳健性诊断：240 日纯动量",
        "",
        *table(report_results),
        "",
        "## 对三层策略的约束",
        "",
        "- A 保留为 6 ETF＋固定 Top3 的实现基线。",
        "- B 保留为固定 16 ETF＋有效池 25% 的扩池实验，但 B−A 不得直接归因于扩池或因子有效。",
        "- C 仅继续完善动态准入、流动性数据和时点审计；在纯动量未通过闸门前不做参数寻优或正式晋级。",
        "- Legacy V1 继续单独保存，只用于历史复现。",
        "",
    ]
    (output_dir / "momentum_validity_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    return payload
