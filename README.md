# Industry ETF Rotation Research

> ⚠️ **Pure-momentum factor gate: `NOT_VALIDATED` — exploratory research, not promoted.**

An internship research portfolio on A-share industry ETF rotation, with an emphasis on point-in-time data controls, reproducible factor testing, and honest separation between attractive backtests and statistically validated evidence.

## Highlights

- Refactored the V2 signal to **252-trading-day pure momentum** after the reversal component failed validation.
- Designed A/B/C experiments for a 6-ETF baseline, a 16-ETF fixed universe, and point-in-time dynamic admission.
- Implemented fail-closed controls for missing admission decisions and empty eligible pools.
- Evaluated RankIC, Top-minus-Bottom spreads, group monotonicity, annual stability, A/B attribution, turnover, and costs.
- Kept the research conclusion at `NOT_VALIDATED`: none of four primary cross-sections passed both 5% significance requirements.

See [INTERNSHIP_PROJECT.md](INTERNSHIP_PROJECT.md) for the research narrative, results, repository map, and reproduction commands.

## Public-safe scope

This repository excludes licensed market data, full daily NAV/position/transaction histories, employer-internal documents, credentials, and personal paths. Only code, tests, frozen configuration, and aggregate research statistics are included. See [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md).

## Run the public checks

```bash
python -m pip install -r requirements-public.txt
python -m pytest -q tests/test_v2_signals.py tests/test_v2_admission.py tests/test_momentum_validity_gate.py
python run_public_gate.py
```

Expected final status: `NOT_VALIDATED`.

## Disclaimer

This project is for research and portfolio presentation only. It is not investment advice, and historical backtests do not represent future performance.

