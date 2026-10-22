import pandas as pd
import pytest

from research_v2.strategy.signals import (
    build_eligible_equal_weight_signals,
    generate_signals,
)


def _prices(columns: int = 4) -> pd.DataFrame:
    dates = pd.date_range("2024-01-02", periods=45, freq="B")
    return pd.DataFrame(
        {
            f"asset_{number}": [100 + number * 10 + day for day in range(45)]
            for number in range(columns)
        },
        index=dates,
        dtype=float,
    )


def test_pure_momentum_does_not_require_turning_or_reversal_history() -> None:
    prices = _prices()

    signals = generate_signals(
        prices,
        pd.DataFrame(),
        momentum_window=5,
        reversal_window=500,
        top_n=1,
        signal_mode="momentum",
    )

    assert not signals.empty
    assert set(signals["direction"]) == {"动量"}
    assert signals["selected_count"].eq(1).all()


def test_fractional_holdings_use_ceiling_of_current_eligible_pool() -> None:
    prices = _prices(columns=5)

    signals = generate_signals(
        prices,
        pd.DataFrame(),
        momentum_window=5,
        top_n=None,
        signal_mode="momentum",
        top_fraction=0.25,
    )

    assert signals["eligible_count"].eq(5).all()
    assert signals["selected_count"].eq(2).all()


def test_admission_mask_is_applied_before_holding_count() -> None:
    prices = _prices(columns=5)
    admission = pd.DataFrame(
        {
            "asset_0": [True],
            "asset_1": [True],
            "asset_2": [False],
            "asset_3": [False],
            "asset_4": [False],
        },
        index=[prices.index[4]],
    )

    signals = generate_signals(
        prices,
        pd.DataFrame(),
        momentum_window=5,
        top_n=None,
        signal_mode="momentum",
        top_fraction=0.25,
        admission_mask=admission,
    )

    assert signals["eligible_count"].eq(2).all()
    assert signals["selected_count"].eq(1).all()
    weight_columns = [column for column in signals if column.startswith("weight_")]
    assert (signals[weight_columns].gt(0).sum(axis=1) == 1).all()


def test_admission_fails_when_first_valid_signal_has_no_prior_decision() -> None:
    prices = _prices(columns=3)
    admission = pd.DataFrame(
        {column: [True] for column in prices.columns},
        index=[prices.index[-1]],
    )

    with pytest.raises(ValueError, match="没有时点可得"):
        generate_signals(
            prices,
            pd.DataFrame(),
            momentum_window=5,
            top_n=1,
            signal_mode="momentum",
            admission_mask=admission,
        )


def test_admission_fails_when_admitted_assets_are_not_factor_eligible() -> None:
    prices = _prices(columns=2)
    prices["asset_1"] = pd.NA
    admission = pd.DataFrame(
        {"asset_0": [False], "asset_1": [True]},
        index=[prices.index[0]],
    )

    with pytest.raises(ValueError, match="实际空池"):
        generate_signals(
            prices,
            pd.DataFrame(),
            momentum_window=5,
            top_n=1,
            signal_mode="momentum",
            admission_mask=admission,
        )


def test_equal_weight_benchmark_uses_exact_signal_eligible_pool() -> None:
    prices = _prices(columns=4)
    prices.loc[: prices.index[20], "asset_3"] = pd.NA
    signals = generate_signals(
        prices,
        pd.DataFrame(),
        momentum_window=5,
        top_n=1,
        signal_mode="momentum",
    )

    benchmark = build_eligible_equal_weight_signals(
        signals,
        list(prices.columns),
    )

    for date, row in benchmark.iterrows():
        score_eligible = [
            asset
            for asset in prices.columns
            if pd.notna(row[f"score_{asset}"])
        ]
        positive_weights = [
            asset
            for asset in prices.columns
            if row[f"weight_{asset}"] > 0
        ]
        assert positive_weights == score_eligible
        assert sum(row[f"weight_{asset}"] for asset in prices.columns) == 1


def test_legacy_turning_keeps_common_momentum_reversal_sample() -> None:
    prices = _prices(columns=3)
    turning = pd.DataFrame(
        {"direction": "反转", "turning_index": 1.0}, index=prices.index
    )

    signals = generate_signals(
        prices,
        turning,
        momentum_window=20,
        reversal_window=5,
        top_n=1,
        signal_mode="turning",
    )

    assert not signals.empty
    assert signals.index.min() >= prices.index[20]
