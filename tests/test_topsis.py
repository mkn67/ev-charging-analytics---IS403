"""Tests import the same production functions used by NV4 pipeline and notebook."""
import numpy as np
import pandas as pd

from src.topsis import entropy_weights, normalize_minmax, topsis, vector_topsis


def test_minmax_respects_benefit_and_cost_directions():
    raw = pd.DataFrame({"benefit": [10.0, 20.0, 30.0], "cost": [2.0, 4.0, 8.0]})
    normalized = normalize_minmax(raw, {"benefit": 1, "cost": -1})
    assert normalized["benefit"].tolist() == [0.0, 0.5, 1.0]
    assert normalized["cost"].tolist() == [1.0, 2 / 3, 0.0]


def test_topsis_dominance_and_entropy_weights():
    normalized = pd.DataFrame({
        "C1": [1.0, 0.5, 0.0],
        "C2": [1.0, 0.6, 0.1],
        "C3": [0.9, 0.4, 0.0],
    }, index=["Alt_A", "Alt_B", "Alt_C"])
    _, weights = entropy_weights(normalized)
    assert np.isclose(weights.sum(), 1.0)
    result = topsis(normalized, weights)
    assert result["Rank"].tolist() == [1, 2, 3]
    assert result["TOPSIS_Score"].between(0, 1).all()


def test_full_precision_score_tie_breaks_by_alternative_name():
    normalized = pd.DataFrame({"C1": [0.5, 0.5], "C2": [0.5, 0.5]}, index=["Station_B", "Station_A"])
    weights = pd.Series([0.5, 0.5], index=normalized.columns)
    result = topsis(normalized, weights)
    assert result.loc["Station_A", "Rank"] == 1
    assert result.loc["Station_B", "Rank"] == 2
    assert result["TOPSIS_Score"].nunique() == 1


def test_vector_topsis_uses_same_deterministic_tie_break():
    raw = pd.DataFrame({"benefit": [1.0, 1.0], "cost": [2.0, 2.0]}, index=["B", "A"])
    result = vector_topsis(raw, {"benefit": 1, "cost": -1}, pd.Series([0.5, 0.5], index=raw.columns))
    assert result.loc["A", "Rank"] == 1
    assert result.loc["B", "Rank"] == 2


def test_constant_criterion_has_finite_normalization_and_equal_entropy_fallback():
    raw = pd.DataFrame({"constant": [3.0, 3.0], "varying": [1.0, 2.0]})
    normalized = normalize_minmax(raw, {"constant": 1, "varying": 1})
    assert normalized.constant.tolist() == [1.0, 1.0]
    _, weights = entropy_weights(pd.DataFrame({"a": [1.0, 1.0], "b": [1.0, 1.0]}))
    assert np.allclose(weights.to_numpy(), [0.5, 0.5])
