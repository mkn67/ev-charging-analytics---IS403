"""Rebuild NV4 validation, criteria, TOPSIS, sensitivity tables, and figures.

Run from any working directory with:
    python scripts/generate_all_nv4_assets.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import RAW_DATA_FILE, SESSIONS_CLEAN_PARQUET
from src.nv4_analysis import NV4_CRITERIA, build_station_criteria, prepare_nv4_sessions
from src.nv4_sensitivity import run_sensitivity
from src.topsis import entropy_weights, normalize_minmax, topsis

OUTPUT_DIR = ROOT / "outputs"
FIG_DIR = OUTPUT_DIR / "figures"
REPORT_FIG_DIR = ROOT / "reports" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FIG_DIR.mkdir(parents=True, exist_ok=True)
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 9


def save_figure(fig, filename):
    for directory in (FIG_DIR, REPORT_FIG_DIR):
        fig.savefig(directory / filename, bbox_inches="tight", dpi=200)
    plt.close(fig)


raw = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig", low_memory=False)
sessions, reconciliation, run_metadata = prepare_nv4_sessions(raw)
all_stations, X = build_station_criteria(sessions)
run_metadata.update({
    "station_count_after_cleaning": int(len(all_stations)),
    "eligible_station_threshold_sessions": 500,
    "eligible_station_count": int(len(X)),
    "sessions_in_eligible_stations": int(X["C1_so_phien"].sum()),
})
if SESSIONS_CLEAN_PARQUET.exists():
    nv1 = pd.read_parquet(SESSIONS_CLEAN_PARQUET)
    parquet_valid = int(nv1["is_valid_session"].sum())
    if parquet_valid != run_metadata["nv1_valid_sessions"]:
        raise AssertionError(f"NV1 valid count mismatch: parquet={parquet_valid}, raw pipeline={run_metadata['nv1_valid_sessions']}")
    run_metadata["sessions_clean_parquet_valid_sessions"] = parquet_valid

reconciliation = pd.concat([
    reconciliation,
    pd.DataFrame([
        {"stage": "Distinct stations after NV4 filters", "rows_remaining": len(all_stations),
         "removed_at_stage": None, "rule": "Unique normalized Station Name"},
        {"stage": "Stations eligible for ranking", "rows_remaining": len(X),
         "removed_at_stage": len(all_stations) - len(X), "rule": "At least 500 NV4-valid sessions"},
        {"stage": "Sessions represented in eligible stations", "rows_remaining": int(X["C1_so_phien"].sum()),
         "removed_at_stage": len(sessions) - int(X["C1_so_phien"].sum()),
         "rule": "Sessions in stations meeting the 500-session threshold"},
    ])
], ignore_index=True)
reconciliation.to_csv(OUTPUT_DIR / "nv4_session_reconciliation.csv", index=False, encoding="utf-8-sig")
pd.Series(run_metadata, name="value").to_json(OUTPUT_DIR / "nv4_run_metadata.json", indent=2, force_ascii=False)

criterion_columns = list(NV4_CRITERIA)
directions = {column: spec[2] for column, spec in NV4_CRITERIA.items()}
labels = {column: spec[0] for column, spec in NV4_CRITERIA.items()}
decision = X[criterion_columns]
R = normalize_minmax(decision, directions)
bang_entropy, w_entropy = entropy_weights(R, labels)
w_equal = pd.Series(1.0 / len(criterion_columns), index=criterion_columns, name="Trọng số đều (w_j)")
top_entropy = topsis(R, w_entropy)
top_equal = topsis(R, w_equal)

rank = pd.DataFrame({
    "Station Name": X.index,
    "C1_so_phien": X["C1_so_phien"],
    "Score_Entropy": top_entropy["TOPSIS_Score"],
    "Rank_Entropy": top_entropy["Rank"],
    "Score_Equal": top_equal["TOPSIS_Score"],
    "Rank_Equal": top_equal["Rank"],
    "Rank_Diff": (top_entropy["Rank"] - top_equal["Rank"]).abs(),
}).reset_index(drop=True).sort_values(["Rank_Entropy", "Station Name"], kind="mergesort")

export_criteria = X[criterion_columns].copy()
export_criteria.to_csv(OUTPUT_DIR / "nv4_station_criteria.csv", encoding="utf-8-sig")
weights_table = bang_entropy[["Tên tiêu chí", "Entropy (e_j)", "Độ phân kỳ (d_j = 1 - e_j)", "Trọng số Entropy (w_j)"]].copy()
weights_table["Trọng số đều (w_j)"] = w_equal
weights_table["Chênh lệch (w_Entropy - w_Equal)"] = weights_table["Trọng số Entropy (w_j)"] - w_equal
weights_table.to_csv(OUTPUT_DIR / "nv4_criteria_weights.csv", encoding="utf-8-sig")
rank.to_csv(OUTPUT_DIR / "nv4_topsis_rankings.csv", index=False, encoding="utf-8-sig")

correlations_pearson = decision.corr(method="pearson")
correlations_spearman = decision.corr(method="spearman")
correlations_pearson.to_csv(OUTPUT_DIR / "nv4_criteria_correlations_pearson.csv", encoding="utf-8-sig")
correlations_spearman.to_csv(OUTPUT_DIR / "nv4_criteria_correlations_spearman.csv", encoding="utf-8-sig")

matrix_labels = ["C1: Số phiên", "C2: Tổng kWh", "C3: kWh/phiên", "C4: Giờ sạc/phiên", "C5: Tỷ lệ nhàn rỗi", "C6: Chiếm dụng nặng"]
fig, ax = plt.subplots(figsize=(6.5, 5), dpi=200)
sns.heatmap(correlations_pearson, annot=True, fmt=".3f", cmap="vlag", vmin=-1, vmax=1,
            ax=ax, xticklabels=matrix_labels, yticklabels=matrix_labels,
            cbar_kws={"label": "Pearson correlation"})
ax.set_title("Tương quan Pearson giữa 6 tiêu chí NV4", fontweight="bold")
plt.xticks(rotation=30, ha="right", fontsize=8)
plt.yticks(fontsize=8)
fig.tight_layout()
save_figure(fig, "hinh_3_4_tuong_quan_tieu_chi.png")

fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
sns.heatmap(R, cmap="YlGnBu", vmin=0, vmax=1, ax=ax,
            yticklabels=[s.replace("PALO ALTO CA / ", "") for s in R.index])
ax.set_title("Ma trận Min-Max của 33 trạm đủ điều kiện")
fig.tight_layout()
save_figure(fig, "hinh_3_5_ma_tran_chuan_hoa.png")

fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
plot_weights = pd.DataFrame({"Entropy": w_entropy, "Equal": w_equal})
plot_weights.index = matrix_labels
plot_weights.plot.bar(ax=ax, color=["#2b6cb0", "#718096"])
ax.set_ylabel("Trọng số")
ax.set_title("Trọng số Entropy và trọng số đều")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save_figure(fig, "hinh_3_6_trong_so.png")

plot_rank = rank.sort_values("Score_Entropy", ascending=True)
station_labels = [s.replace("PALO ALTO CA / ", "") for s in plot_rank["Station Name"]]
fig, ax = plt.subplots(figsize=(8, 9), dpi=200)
y = np.arange(len(plot_rank))
ax.barh(y - .18, plot_rank["Score_Entropy"], height=.35, label="Entropy", color="#2b6cb0")
ax.barh(y + .18, plot_rank["Score_Equal"], height=.35, label="Trọng số đều", color="#718096", alpha=.85)
ax.set_yticks(y, station_labels, fontsize=7.5)
ax.set_xlabel("Điểm TOPSIS")
ax.set_title(f"TOPSIS của {len(rank)} trạm")
ax.legend(loc="lower right")
fig.tight_layout()
save_figure(fig, "hinh_3_7_diem_topsis.png")

fig, ax = plt.subplots(figsize=(7, 10), dpi=200)
for _, row in rank.iterrows():
    name = row["Station Name"].replace("PALO ALTO CA / ", "")
    ax.plot([0, 1], [row["Rank_Entropy"], row["Rank_Equal"]], marker="o", linewidth=1.2)
    ax.text(-.03, row["Rank_Entropy"], f"{row['Rank_Entropy']}. {name}", ha="right", va="center", fontsize=6.5)
    ax.text(1.03, row["Rank_Equal"], f"{row['Rank_Equal']}. {name}", ha="left", va="center", fontsize=6.5)
ax.set_xticks([0, 1], ["Entropy", "Đều"])
ax.set_ylim(len(rank) + 1, 0)
ax.set_ylabel("Hạng")
ax.set_title("So sánh hạng theo hai bộ trọng số")
ax.spines[["top", "right", "bottom"]].set_visible(False)
fig.tight_layout()
save_figure(fig, "hinh_3_8_so_sanh_thu_hang.png")

fig, ax = plt.subplots(figsize=(6.5, 6), dpi=200)
ax.scatter(rank["Score_Entropy"], rank["Score_Equal"], color="#2b6cb0", edgecolors="white", s=60)
ax.plot([rank.Score_Entropy.min(), rank.Score_Entropy.max()],
        [rank.Score_Entropy.min(), rank.Score_Entropy.max()], "r--", alpha=.7)
ax.set_xlabel("Điểm TOPSIS (Entropy)")
ax.set_ylabel("Điểm TOPSIS (Đều)")
ax.set_title("So sánh điểm TOPSIS")
fig.tight_layout()
save_figure(fig, "hinh_3_9_phan_tan_diem.png")

sensitivity = run_sensitivity(X, NV4_CRITERIA)
sensitivity.to_csv(OUTPUT_DIR / "nv4_sensitivity_analysis.csv", index=False, encoding="utf-8-sig")
sens_plot = sensitivity.loc[sensitivity.Scenario.str.match(r"S[1-6]:")].copy()
if sens_plot.empty:
    sens_plot = sensitivity.iloc[1:].copy()
fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
positions = np.arange(len(sens_plot))
ax.bar(positions - .18, sens_plot["Spearman_Entropy"], width=.35, label="Spearman", color="#2b6cb0")
ax.bar(positions + .18, sens_plot["Kendall_Entropy"], width=.35, label="Kendall", color="#4fd1c5")
ax.set_xticks(positions, sens_plot["Scenario"].str.split(":").str[0])
ax.set_ylim(.5, 1.08)
ax.set_ylabel("Tương quan hạng với S0")
ax.set_title("Độ nhạy TOPSIS")
ax.legend()
fig.tight_layout()
save_figure(fig, "hinh_3_10_phan_tich_do_nhay.png")

rho_c5_c6 = float(correlations_spearman.loc["C5_ty_le_nhan_roi", "C6_ty_le_chiem_dung_nghiem_trong"])
rho_baseline = float(spearmanr(rank["Rank_Entropy"], rank["Rank_Equal"]).statistic)
tau_baseline = float(kendalltau(rank["Rank_Entropy"], rank["Rank_Equal"]).statistic)
print("NV4 reconciliation:\n", reconciliation.to_string(index=False))
print("Entropy weights:\n", weights_table.to_string())
print(f"Spearman(C5,C6)={rho_c5_c6:.6f}; rank agreement Spearman={rho_baseline:.6f}, Kendall={tau_baseline:.6f}")
print("Generated all NV4 outputs in", OUTPUT_DIR)
