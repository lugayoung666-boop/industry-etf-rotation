# Runnable Baseline Freeze

This repository is currently frozen at a runnable single-layer ETF rotation
baseline before the V2 three-layer strategy is implemented.

## Baseline Command

```powershell
python run_backtest.py --source local --output output_baseline_freeze
```

## Runtime Configuration

The baseline uses `config/strategy.yaml`.

Important parameters:

```yaml
rank_return_window: 21
rank_change_lag: 21
rank_vol_window: 220
rank_smooth_window: 20
momentum_window: 252
reversal_window: 63
top_n: 3
signal_mode: turning
fee: 0.0005
slippage: 0.0005
initial_cash: 1000000
```

`config/strategy_report_params.yaml` is kept consistent with the runtime
`rank_change_lag: 21` to avoid report/runtime parameter drift.

## Data Alignment Rule

`data/cache.py` no longer truncates every ETF to the latest common start date.
Each ETF is clipped independently to the requested date range. After pivoting,
newly listed ETFs are `NaN` before their own listing date, so expanding the ETF
universe will not move the whole backtest start date forward.

## Smoke Result

Generated on the uploaded local cache with:

```powershell
python run_backtest.py --source local --output output_baseline_freeze
```

| Metric | Value |
|---|---:|
| Cumulative return | 0.690121 |
| Annual return | 0.046606 |
| Annual volatility | 0.188650 |
| Sharpe | 0.344760 |
| Max drawdown | -0.400935 |
| Calmar | 0.116242 |
| Win rate | 0.439643 |
| Rebalance count | 119 |
| Average turnover | 0.613445 |
| Trading cost | 110382.730848 |
