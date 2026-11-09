"""Reproducible NV4 ranking sensitivity scenarios S0-S6."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from .topsis import entropy_weights, normalize_minmax, topsis, vector_topsis

S5_LABEL = "Tỷ lệ thời gian nhàn rỗi trọng số"


def _directions(criteria):
    return {column: spec[2] for column, spec in criteria.items()}


def _evaluate(name, decision, criteria, baseline_entropy, baseline_equal):
    normalized = normalize_minmax(decision, _directions(criteria))
    _, weights_entropy = entropy_weights(normalized, {c: criteria[c][0] for c in criteria})
    weights_equal = pd.Series(1.0 / len(criteria), index=decision.columns)
    ranked_entropy = topsis(normalized, weights_entropy)
    ranked_equal = topsis(normalized, weights_equal)

    def compare(current, baseline):
        delta = (current["Rank"] - baseline).abs()
        overlap = len(set(current.nsmallest(5, "Rank").index) & set(baseline.nsmallest(5).index))
        return {
            "Spearman": float(spearmanr(current["Rank"], baseline).statistic),
            "Kendall": float(kendalltau(current["Rank"], baseline).statistic),
            "Mean_Rank_Diff": float(delta.mean()),
            "Max_Rank_Diff": int(delta.max()),
            "Stations_Diff_ge5": int(delta.ge(5).sum()),
            "Top5_Overlap": f"{overlap}/5",
        }

    ent = compare(ranked_entropy, baseline_entropy)
    equ = compare(ranked_equal, baseline_equal)
    row = {
        "Scenario": name, "Criteria_Count": len(criteria),
        "Spearman_Entropy": round(ent["Spearman"], 4),
        "Kendall_Entropy": round(ent["Kendall"], 4),
        "Mean_Rank_Diff_Entropy": round(ent["Mean_Rank_Diff"], 2),
        "Max_Rank_Diff_Entropy": ent["Max_Rank_Diff"],
        "Stations_Diff_ge5_Entropy": ent["Stations_Diff_ge5"],
        "Top5_Overlap_Entropy": ent["Top5_Overlap"],
        "Spearman_Equal": round(equ["Spearman"], 4),
        "Kendall_Equal": round(equ["Kendall"], 4),
        "Mean_Rank_Diff_Equal": round(equ["Mean_Rank_Diff"], 2),
        "Max_Rank_Diff_Equal": equ["Max_Rank_Diff"],
        "Stations_Diff_ge5_Equal": equ["Stations_Diff_ge5"],
        "Top5_Overlap_Equal": equ["Top5_Overlap"],
    }
    return row, ranked_entropy, ranked_equal


def run_sensitivity(matrix: pd.DataFrame, criteria: dict):
    """Run full criteria baseline, five criterion variants, and vector S6."""
    baseline_matrix = matrix[list(criteria)]
    baseline_norm = normalize_minmax(baseline_matrix, _directions(criteria))
    _, weights_entropy = entropy_weights(baseline_norm, {c: criteria[c][0] for c in criteria})
    weights_equal = pd.Series(1.0 / len(criteria), index=baseline_matrix.columns)
    baseline_entropy = topsis(baseline_norm, weights_entropy)["Rank"]
    baseline_equal = topsis(baseline_norm, weights_equal)["Rank"]

    rows = []
    row0, _, _ = _evaluate("S0: Gốc (C1-C6)", baseline_matrix, criteria, baseline_entropy, baseline_equal)
    rows.append(row0)
    scenarios = [
        ("S1: Loại C2 (Tổng kWh)", "C2_tong_dien_nang"),
        ("S2: Loại C1 (Số phiên)", "C1_so_phien"),
        ("S3: Loại C6 (Chiếm dụng nặng)", "C6_ty_le_chiem_dung_nghiem_trong"),
        ("S4: Loại C4 (Thời gian sạc)", "C4_gio_sac_moi_phien"),
    ]
    for name, omitted in scenarios:
        columns = [c for c in criteria if c != omitted]
        row, _, _ = _evaluate(name, matrix[columns], {c: criteria[c] for c in columns},
                              baseline_entropy, baseline_equal)
        rows.append(row)

    s5_criteria = dict(criteria)
    s5_criteria.pop("C5_ty_le_nhan_roi")
    s5_criteria["C5_weighted"] = (S5_LABEL, "tỷ lệ", -1)
    s5_columns = [c for c in criteria if c != "C5_ty_le_nhan_roi"]
    s5_columns.insert(4, "C5_weighted")
    row, _, _ = _evaluate("S5: C5 trọng số thời lượng", matrix[s5_columns], s5_criteria,
                          baseline_entropy, baseline_equal)
    rows.append(row)

    vector = vector_topsis(baseline_matrix, _directions(criteria), weights_entropy)
    delta = (vector["Rank"] - baseline_entropy).abs()
    overlap = len(set(vector.nsmallest(5, "Rank").index) & set(baseline_entropy.nsmallest(5).index))
    rows.append({
        "Scenario": "S6: Vector Normalization", "Criteria_Count": len(criteria),
        "Spearman_Entropy": round(float(spearmanr(vector["Rank"], baseline_entropy).statistic), 4),
        "Kendall_Entropy": round(float(kendalltau(vector["Rank"], baseline_entropy).statistic), 4),
        "Mean_Rank_Diff_Entropy": round(float(delta.mean()), 2),
        "Max_Rank_Diff_Entropy": int(delta.max()),
        "Stations_Diff_ge5_Entropy": int(delta.ge(5).sum()),
        "Top5_Overlap_Entropy": f"{overlap}/5",
        "Spearman_Equal": np.nan, "Kendall_Equal": np.nan,
        "Mean_Rank_Diff_Equal": np.nan, "Max_Rank_Diff_Equal": np.nan,
        "Stations_Diff_ge5_Equal": np.nan, "Top5_Overlap_Equal": "N/A",
    })
    return pd.DataFrame(rows)
