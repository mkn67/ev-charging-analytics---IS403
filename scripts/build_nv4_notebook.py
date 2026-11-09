"""Build the NV4 notebook as a thin, reproducible front end to src modules."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cells = []


def markdown(source):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)})


def code(source):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                  "source": source.splitlines(keepends=True)})


markdown("""# NV4 — Đánh giá hiệu suất mạng lưới trạm sạc

Notebook này dùng trực tiếp các hàm production trong `src/nv4_analysis.py`, `src/topsis.py` và `src/nv4_sensitivity.py`. Chạy cell theo thứ tự. Ledger ở bước 2 đối soát dữ liệu NV1 → NV4; cell cuối lưu bảng từ cùng lượt tính.

Quy tắc hiện hành: parser ngày và quy đổi PDT/PST/UTC theo NV1; ngưỡng công suất lấy từ `src.config.POWER_LIMITS_KW` theo `Port Type`; kiểm tra chênh lệch giữa thời lượng phiên và thời gian bắt đầu/kết thúc tối đa 59 giây. TOPSIS xếp theo điểm đầy đủ trước khi làm tròn; nếu điểm bằng nhau chính xác, tên trạm tăng dần là tiêu chí phụ.""")

markdown("## 1. Thiết lập")
code("""from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr
from IPython.display import display

ROOT = Path.cwd()
while not (ROOT / "src" / "config.py").exists():
    if ROOT.parent == ROOT:
        raise RuntimeError("Open this notebook from the project workspace")
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from src.config import RAW_DATA_FILE, SESSIONS_CLEAN_PARQUET, POWER_LIMITS_KW
from src.nv4_analysis import NV4_CRITERIA, build_station_criteria, prepare_nv4_sessions
from src.nv4_sensitivity import run_sensitivity
from src.topsis import entropy_weights, normalize_minmax, topsis

OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print("Source:", RAW_DATA_FILE)
print("Power limits by Port Type:", POWER_LIMITS_KW)""")

markdown("""## 2. Nạp dữ liệu và đối soát NV1 → NV4

Các dòng bị loại trong ledger là các bước tuần tự, không cộng trùng. Dòng `NV1 is_valid_session` là mốc đối chiếu độc lập. Dòng cuối cùng tách riêng số phiên bị NV4 loại thêm do kiểm tra timestamp.""")
code("""raw = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig", low_memory=False)
sessions, reconciliation, run_metadata = prepare_nv4_sessions(raw)
all_stations, X = build_station_criteria(sessions)
run_metadata.update({
    "station_count_after_cleaning": len(all_stations),
    "eligible_station_count": len(X),
    "sessions_in_eligible_stations": int(X["C1_so_phien"].sum()),
})
if SESSIONS_CLEAN_PARQUET.exists():
    nv1_clean = pd.read_parquet(SESSIONS_CLEAN_PARQUET)
    parquet_valid = int(nv1_clean["is_valid_session"].sum())
    if parquet_valid != run_metadata["nv1_valid_sessions"]:
        raise AssertionError(f"NV1 count mismatch: parquet={parquet_valid}, raw={run_metadata['nv1_valid_sessions']}")
    run_metadata["sessions_clean_parquet_valid_sessions"] = parquet_valid

reconciliation = pd.concat([reconciliation, pd.DataFrame([
    {"stage": "Distinct stations after NV4 filters", "rows_remaining": len(all_stations),
     "removed_at_stage": None, "rule": "Unique normalized Station Name"},
    {"stage": "Stations eligible for ranking", "rows_remaining": len(X),
     "removed_at_stage": len(all_stations)-len(X), "rule": "At least 500 NV4-valid sessions"},
    {"stage": "Sessions in eligible stations", "rows_remaining": int(X.C1_so_phien.sum()),
     "removed_at_stage": len(sessions)-int(X.C1_so_phien.sum()),
     "rule": "Sessions in stations meeting the threshold"},
])], ignore_index=True)
display(reconciliation)
display(pd.Series(run_metadata, name="value").to_frame())""")

markdown("## 3. Tiêu chí và tương quan")
code("""criterion_columns = list(NV4_CRITERIA)
directions = {c: NV4_CRITERIA[c][2] for c in criterion_columns}
labels = {c: NV4_CRITERIA[c][0] for c in criterion_columns}
decision = X[criterion_columns]
corr_pearson = decision.corr(method="pearson")
corr_spearman = decision.corr(method="spearman")
display(decision.head())
display(corr_pearson.round(4))
display(corr_spearman.round(4))
print("Spearman(C5,C6):", corr_spearman.loc["C5_ty_le_nhan_roi", "C6_ty_le_chiem_dung_nghiem_trong"])""")

markdown("## 4. Min-Max, Entropy và TOPSIS")
code("""R = normalize_minmax(decision, directions)
entropy_table, w_entropy = entropy_weights(R, labels)
w_equal = pd.Series(1.0 / len(criterion_columns), index=criterion_columns, name="Trọng số đều")
display(entropy_table.round(6))

top_entropy = topsis(R, w_entropy)
top_equal = topsis(R, w_equal)
df_rank = pd.DataFrame({
    "Station Name": X.index.to_numpy(),
    "C1_so_phien": X["C1_so_phien"].to_numpy(),
    "Score_Entropy": top_entropy["TOPSIS_Score"].to_numpy(),
    "Rank_Entropy": top_entropy["Rank"].to_numpy(),
    "Score_Equal": top_equal["TOPSIS_Score"].to_numpy(),
    "Rank_Equal": top_equal["Rank"].to_numpy(),
})
df_rank["Rank_Diff"] = (df_rank.Rank_Entropy - df_rank.Rank_Equal).abs()
df_rank = df_rank.sort_values(["Rank_Entropy", "Station Name"], kind="mergesort").reset_index(drop=True)
display(df_rank)
display(df_rank.head(5))
display(df_rank.tail(5))
print("Baseline Spearman:", spearmanr(df_rank.Rank_Entropy, df_rank.Rank_Equal).statistic)
print("Baseline Kendall:", kendalltau(df_rank.Rank_Entropy, df_rank.Rank_Equal).statistic)
print("Mean/max rank difference:", df_rank.Rank_Diff.mean(), df_rank.Rank_Diff.max())""")

markdown("## 5. Kiểm tra độ nhạy S0–S6")
code("""df_sensitivity = run_sensitivity(X, NV4_CRITERIA)
display(df_sensitivity)""")

markdown("## 6. Lưu bảng kết quả")
code("""reconciliation.to_csv(OUTPUT_DIR / "nv4_session_reconciliation.csv", index=False, encoding="utf-8-sig")
pd.Series(run_metadata, name="value").to_json(OUTPUT_DIR / "nv4_run_metadata.json", indent=2, force_ascii=False)
X[criterion_columns].to_csv(OUTPUT_DIR / "nv4_station_criteria.csv", encoding="utf-8-sig")
entropy_table.to_csv(OUTPUT_DIR / "nv4_criteria_weights.csv", encoding="utf-8-sig")
df_rank.to_csv(OUTPUT_DIR / "nv4_topsis_rankings.csv", index=False, encoding="utf-8-sig")
corr_pearson.to_csv(OUTPUT_DIR / "nv4_criteria_correlations_pearson.csv", encoding="utf-8-sig")
corr_spearman.to_csv(OUTPUT_DIR / "nv4_criteria_correlations_spearman.csv", encoding="utf-8-sig")
df_sensitivity.to_csv(OUTPUT_DIR / "nv4_sensitivity_analysis.csv", index=False, encoding="utf-8-sig")
print("Saved NV4 tables from this run to", OUTPUT_DIR)""")

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
path = ROOT / "notebooks" / "04_NV4_station_benchmarking.ipynb"
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print("Built", path)
