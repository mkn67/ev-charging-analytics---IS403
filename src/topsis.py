"""Shared Min-Max, entropy weighting, and deterministic TOPSIS functions."""
from __future__ import annotations

import numpy as np
import pandas as pd

ENTROPY_COL = "Entropy (e_j)"
DIVERGENCE_COL = "Độ phân kỳ (d_j = 1 - e_j)"
WEIGHT_COL = "Trọng số Entropy (w_j)"
LABEL_COL = "Tên tiêu chí"


def normalize_minmax(decision: pd.DataFrame, directions: dict[str, int]) -> pd.DataFrame:
    """Normalize benefit/cost criteria to [0, 1]; constants map to 1."""
    if decision.empty:
        raise ValueError("Decision matrix must contain at least one station")
    if set(decision.columns) != set(directions):
        raise ValueError("Directions must define every decision-matrix column exactly once")
    normalized = pd.DataFrame(index=decision.index, columns=decision.columns, dtype=float)
    for column in decision:
        values = pd.to_numeric(decision[column], errors="raise").astype(float)
        if not np.isfinite(values.to_numpy()).all():
            raise ValueError(f"Non-finite values in criterion {column!r}")
        low, high = values.min(), values.max()
        if directions[column] not in (-1, 1):
            raise ValueError(f"Direction for {column!r} must be +1 (benefit) or -1 (cost)")
        if high == low:
            normalized[column] = 1.0
        elif directions[column] > 0:
            normalized[column] = (values - low) / (high - low)
        else:
            normalized[column] = (high - values) / (high - low)
    return normalized


def entropy_weights(
    normalized: pd.DataFrame,
    labels: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """Calculate Shannon entropy and normalized divergence weights."""
    m = len(normalized)
    if m < 2 or normalized.shape[1] < 1:
        raise ValueError("Entropy weighting requires at least two stations and one criterion")
    if (normalized < 0).any().any() or not np.isfinite(normalized.to_numpy(dtype=float)).all():
        raise ValueError("Entropy input must be finite and nonnegative")
    k = 1.0 / np.log(m)
    rows = []
    for column in normalized:
        values = normalized[column].to_numpy(dtype=float)
        total = values.sum()
        p = np.full(m, 1.0 / m) if total == 0 else values / total
        entropy = -k * np.sum(np.where(p > 0, p * np.log(np.where(p > 0, p, 1.0)), 0.0))
        rows.append({ENTROPY_COL: float(entropy), DIVERGENCE_COL: float(1 - entropy)})
    table = pd.DataFrame(rows, index=normalized.columns)
    table.index.name = "Tiêu chí"
    divergence_sum = table[DIVERGENCE_COL].sum()
    if divergence_sum <= 0:
        weights = pd.Series(1.0 / normalized.shape[1], index=normalized.columns, name=WEIGHT_COL)
    else:
        weights = table[DIVERGENCE_COL].div(divergence_sum).rename(WEIGHT_COL)
    table[WEIGHT_COL] = weights
    table[LABEL_COL] = [labels.get(c, c) if labels else c for c in table.index]
    return table, weights


def topsis(normalized: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    """Score and rank alternatives; exact score ties break by station name.

    Ranking uses full-precision scores. Ties in the full-precision score are
    ordered lexicographically by the alternative index, with stable sorting.
    """
    weights = pd.Series(weights, dtype=float).reindex(normalized.columns)
    if weights.isna().any() or (weights < 0).any() or not np.isclose(weights.sum(), 1.0):
        raise ValueError("Weights must be nonnegative, aligned to criteria, and sum to one")
    weighted = normalized.multiply(weights, axis=1)
    positive = weighted.max(axis=0)
    negative = weighted.min(axis=0)
    d_positive = np.sqrt(((weighted - positive) ** 2).sum(axis=1))
    d_negative = np.sqrt(((weighted - negative) ** 2).sum(axis=1))
    denominator = d_positive + d_negative
    score = pd.Series(np.where(denominator == 0, 0.5, d_negative / denominator), index=normalized.index)
    order = pd.DataFrame({"score": score, "alternative": normalized.index.astype(str)}, index=normalized.index)
    order = order.sort_values(["score", "alternative"], ascending=[False, True], kind="mergesort")
    ranks = pd.Series(np.arange(1, len(order) + 1), index=order.index, dtype=int)
    return pd.DataFrame({"D_plus": d_positive, "D_minus": d_negative,
                         "TOPSIS_Score": score, "Rank": ranks})


def vector_topsis(
    decision: pd.DataFrame,
    directions: dict[str, int],
    weights: pd.Series,
) -> pd.DataFrame:
    """Classic vector-normalized TOPSIS used for sensitivity scenario S6."""
    if set(decision.columns) != set(directions):
        raise ValueError("Directions must define every decision-matrix column exactly once")
    weights = pd.Series(weights, dtype=float).reindex(decision.columns)
    if weights.isna().any() or (weights < 0).any() or not np.isclose(weights.sum(), 1.0):
        raise ValueError("Weights must be nonnegative, aligned to criteria, and sum to one")
    norms = np.sqrt((decision.astype(float) ** 2).sum(axis=0)).replace(0, 1.0)
    weighted = decision.astype(float).div(norms, axis=1).multiply(weights, axis=1)
    positive, negative = {}, {}
    for column in decision:
        if directions[column] > 0:
            positive[column], negative[column] = weighted[column].max(), weighted[column].min()
        else:
            positive[column], negative[column] = weighted[column].min(), weighted[column].max()
    d_positive = np.sqrt(((weighted - pd.Series(positive)) ** 2).sum(axis=1))
    d_negative = np.sqrt(((weighted - pd.Series(negative)) ** 2).sum(axis=1))
    denominator = d_positive + d_negative
    score = pd.Series(np.where(denominator == 0, 0.5, d_negative / denominator), index=decision.index)
    order = pd.DataFrame({"score": score, "alternative": decision.index.astype(str)}, index=decision.index)
    order = order.sort_values(["score", "alternative"], ascending=[False, True], kind="mergesort")
    ranks = pd.Series(np.arange(1, len(order) + 1), index=order.index, dtype=int)
    return pd.DataFrame({"TOPSIS_Score": score, "Rank": ranks})
