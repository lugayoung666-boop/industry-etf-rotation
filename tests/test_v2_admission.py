import pandas as pd
import pytest

from research_v2.strategy.admission import (
    admission_audit,
    admission_coverage_audit,
    load_admission_mask,
    summarize_admission,
)


def test_load_admission_mask_parses_and_audits_decisions(tmp_path) -> None:
    path = tmp_path / "admission.csv"
    pd.DataFrame(
        {
            "date": ["2024-01-31", "2024-02-29"],
            "a": [1, 0],
            "b": ["true", "yes"],
        }
    ).to_csv(path, index=False)

    mask = load_admission_mask(path, ["a", "b"])

    assert mask.dtypes.tolist() == [bool, bool]
    assert mask.sum(axis=1).tolist() == [2, 1]
    assert len(admission_audit(mask)) == 4
    assert summarize_admission(mask)["admitted_count_mean"] == 1.5


def test_load_admission_mask_rejects_empty_pool(tmp_path) -> None:
    path = tmp_path / "admission.csv"
    pd.DataFrame(
        {"date": ["2024-01-31"], "a": [False], "b": [False]}
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="空池"):
        load_admission_mask(path, ["a", "b"])


def test_load_admission_mask_requires_exact_asset_columns(tmp_path) -> None:
    path = tmp_path / "admission.csv"
    pd.DataFrame({"date": ["2024-01-31"], "a": [True]}).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="缺少标的列"):
        load_admission_mask(path, ["a", "b"])


def test_admission_coverage_records_applied_point_in_time_decision() -> None:
    mask = pd.DataFrame(
        {"a": [True, False], "b": [False, True]},
        index=pd.to_datetime(["2024-01-31", "2024-02-28"]),
    )

    audit = admission_coverage_audit(
        mask,
        pd.to_datetime(["2024-02-01", "2024-02-29"]),
    )

    assert audit["decision_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-31",
        "2024-02-28",
    ]
    assert audit["decision_age_days"].tolist() == [1, 1]
    assert audit["covered"].all()
