import numpy as np
import pandas as pd
import pytest


def run_topsis(R, w):
    """
    Min-Max-based TOPSIS:
    R: normalized decision matrix (all criteria benefit-oriented, in [0, 1])
    w: weight vector (sums to 1, length equals R.shape[1])
    """
    if isinstance(w, (list, np.ndarray)):
        w = pd.Series(w, index=R.columns)
    
    # 1. Weighted normalized matrix
    V = R.multiply(w, axis=1)
    
    # 2. Positive and negative ideal solutions
    A_plus = V.max(axis=0)
    A_minus = V.min(axis=0)
    
    # 3. Separation Euclidean distances
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    
    # 4. Relative closeness coefficient
    total_d = D_plus + D_minus
    CC = np.where(total_d == 0, 0.5, D_minus / total_d)
    
    res = pd.DataFrame({
        "D_plus": D_plus,
        "D_minus": D_minus,
        "TOPSIS_Score": CC,
    }, index=R.index)
    res["Rank"] = res["TOPSIS_Score"].rank(ascending=False, method="min").astype(int)
    return res


def test_topsis_dominance():
    # Synthetic test where Alt_A dominates Alt_B dominates Alt_C
    # 3 alternatives, 3 criteria (all benefit, normalized in [0, 1])
    R = pd.DataFrame({
        "C1": [1.0, 0.5, 0.0],
        "C2": [1.0, 0.6, 0.1],
        "C3": [0.9, 0.4, 0.0]
    }, index=["Alt_A", "Alt_B", "Alt_C"])
    
    w = pd.Series([0.4, 0.3, 0.3], index=R.columns)
    res = run_topsis(R, w)
    
    assert res.loc["Alt_A", "Rank"] == 1
    assert res.loc["Alt_B", "Rank"] == 2
    assert res.loc["Alt_C", "Rank"] == 3
    assert res.loc["Alt_A", "TOPSIS_Score"] > res.loc["Alt_B", "TOPSIS_Score"]
    assert res.loc["Alt_B", "TOPSIS_Score"] > res.loc["Alt_C", "TOPSIS_Score"]
    assert 0.0 <= res["TOPSIS_Score"].min() <= 1.0
    assert 0.0 <= res["TOPSIS_Score"].max() <= 1.0


def test_topsis_identical_alternatives():
    # When alternatives are identical, scores should be equal and well-defined
    R = pd.DataFrame({
        "C1": [0.5, 0.5],
        "C2": [0.5, 0.5]
    }, index=["Alt_1", "Alt_2"])
    w = pd.Series([0.5, 0.5], index=R.columns)
    res = run_topsis(R, w)
    
    assert res.loc["Alt_1", "TOPSIS_Score"] == 0.5
    assert res.loc["Alt_2", "TOPSIS_Score"] == 0.5
    assert res.loc["Alt_1", "Rank"] == 1
    assert res.loc["Alt_2", "Rank"] == 1


def test_topsis_single_criterion():
    R = pd.DataFrame({
        "C1": [1.0, 0.0]
    }, index=["Best", "Worst"])
    w = pd.Series([1.0], index=R.columns)
    res = run_topsis(R, w)
    
    assert res.loc["Best", "TOPSIS_Score"] == 1.0
    assert res.loc["Worst", "TOPSIS_Score"] == 0.0
    assert res.loc["Best", "Rank"] == 1
    assert res.loc["Worst", "Rank"] == 2

