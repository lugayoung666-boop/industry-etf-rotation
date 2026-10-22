"""Re-run the public momentum promotion gate from aggregate statistics only."""

from __future__ import annotations

import argparse
from pathlib import Path

from research_v2.analysis.momentum_validity_gate import (
    REPORT_SOURCES,
    RUNTIME_SOURCES,
    evaluate_momentum,
    load_momentum_rows,
    write_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recompute the public pure-momentum validation gate."
    )
    parser.add_argument(
        "--input", default="reports/momentum_validity_summary.csv"
    )
    parser.add_argument("--output", default="output_public_gate")
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    input_path = root / args.input
    rows = load_momentum_rows(input_path)
    runtime = evaluate_momentum(rows, sources=RUNTIME_SOURCES, alpha=args.alpha)
    robustness = evaluate_momentum(
        rows, sources=REPORT_SOURCES, alpha=args.alpha
    )
    payload = write_outputs(
        root / args.output,
        runtime,
        robustness,
        input_path=input_path,
        alpha=args.alpha,
    )
    print(payload["status"])
    print(payload["interpretation"])


if __name__ == "__main__":
    main()

