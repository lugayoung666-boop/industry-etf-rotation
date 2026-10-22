# Industry ETF Rotation — Internship Research Portfolio

> **Research gate: `NOT_VALIDATED`. This project remains exploratory and was not promoted to a live strategy.**

## What I built

This project develops and audits an A-share industry ETF rotation workflow. The work covers signal construction, point-in-time eligibility, transaction-cost-aware backtesting, factor validation, robustness checks, and interactive reporting.

The V2 research design removes the ineffective reversal switch and fixes the primary signal to 252-trading-day momentum. Three experimental layers are kept conceptually separate:

- **A:** six-ETF baseline with fixed Top 3 holdings;
- **B:** sixteen-ETF fixed universe with approximately 25% holdings;
- **C:** point-in-time dynamic admission followed by the same momentum ranking.

## Research discipline

The key contribution is not a selected high-return backtest. It is a fail-closed research process:

1. Use only information available by each signal date.
2. Form signals at month-end and execute on the next trading day.
3. Reject missing admission decisions and empty eligible pools.
4. Preserve price anomalies for explicit audit instead of silently smoothing them.
5. Require both positive, statistically significant RankIC and positive, statistically significant Top-minus-Bottom spreads before promotion.

## Main conclusion

All four 252-day cross-sections had positive point estimates, but none passed the pre-declared dual 5% significance gate.

| Cross-section | RankIC | p-value | Top−Bottom | p-value | Gate |
|---|---:|---:|---:|---:|:---:|
| Industry level 1 | 0.0516 | 0.0962 | 0.72% | 0.1732 | Fail |
| Industry level 2 | 0.0352 | 0.1617 | 0.68% | 0.1600 | Fail |
| 6 ETF | 0.0496 | 0.3279 | 1.10% | 0.1106 | Fail |
| 16 ETF | 0.0340 | 0.4211 | 0.65% | 0.3366 | Fail |

The correct interpretation is therefore `NOT_VALIDATED`: the engineering framework is usable for further research, while the current factor evidence does not justify strategy promotion.

## Public repository map

```text
research_v2/
├── strategy/
│   ├── signals.py       # momentum ranking and eligible-pool selection
│   └── admission.py     # point-in-time admission and coverage audit
├── analysis/
│   └── momentum_validity_gate.py
└── config/              # frozen A/B/C experiment settings
reports/                 # aggregate outputs only; no licensed source data
tests/                   # unit tests for V2 controls and validation gate
run_public_gate.py       # reproduces NOT_VALIDATED from aggregate statistics
PUBLIC_DATA_POLICY.md
```

## Quick check

```bash
python -m pip install -r requirements-public.txt
python -m pytest -q tests/test_v2_signals.py tests/test_v2_admission.py tests/test_momentum_validity_gate.py
python run_public_gate.py
```

Expected gate output:

```text
NOT_VALIDATED
```

## Skills demonstrated

- Python, pandas, pytest, YAML configuration
- Cross-sectional momentum research and RankIC diagnostics
- Time-alignment controls and point-in-time universe construction
- Transaction-cost and turnover analysis
- Reproducibility metadata and fail-closed data validation
- Clear separation between exploratory backtests and validated evidence

## Limitations

- Aggregate results are historical and sample-specific.
- The public branch excludes licensed data, so it does not reproduce the full market-data pipeline.
- The dynamic-admission and weighting experiments remain exploratory.
- Historical backtests do not represent future performance and are not investment advice.

