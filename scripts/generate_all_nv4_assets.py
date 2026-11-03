import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, kendalltau

sys.stdout.reconfigure(encoding='utf-8')

# Setup style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

# Paths
BASE_DIR = Path(".")
DATA_PATH = BASE_DIR / "data" / "raw" / "EVChargingStationUsage.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
FIG_DIR = OUTPUT_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# 1. Pipeline
def giay(s):
    try:
        h, m, gi = str(s).split(":")
        return int(h) * 3600 + int(m) * 60 + int(gi)
    except Exception:
        return np.nan

df_raw = pd.read_csv(DATA_PATH, encoding="utf-8-sig", low_memory=False)
df_raw["total_s"] = df_raw["Total Duration (hh:mm:ss)"].map(giay)
df_raw["charging_s"] = df_raw["Charging Time (hh:mm:ss)"].map(giay)
df_raw["total_h"] = df_raw["total_s"] / 3600
df_raw["charging_h"] = df_raw["charging_s"] / 3600
df_raw["energy_kwh"] = pd.to_numeric(df_raw["Energy (kWh)"], errors="coerce")

df = df_raw.drop_duplicates().copy()
df = df[df["total_h"].gt(0) & df["charging_h"].gt(0) & df["charging_h"].le(df["total_h"])]
df = df[(df["energy_kwh"] / df["charging_h"]).le(19.2)]

bat_dau = pd.to_datetime(df["Start Date"], errors="coerce")
ket_thuc = pd.to_datetime(df["End Date"], errors="coerce")
lech_giay = (df["total_s"] - (ket_thuc - bat_dau).dt.total_seconds()).abs()
df = df[lech_giay.le(59)].copy()

df["Station Name"] = (df["Station Name"].str.replace(r"\s+", " ", regex=True).str.strip()
                      .str.replace("BRYANT # 1", "BRYANT #1", regex=False))

df["idle_h"] = (df["total_h"] - df["charging_h"]).clip(lower=0)
df["idle_ratio"] = df["idle_h"] / df["total_h"]
df["chiem_dung_nghiem_trong"] = df["idle_ratio"].gt(0.5).astype(int)

# Assertions
assert len(df) == 258720, f"Expected 258,720 valid sessions, got {len(df)}"
assert df["Station Name"].nunique() == 46, f"Expected 46 distinct stations, got {df['Station Name'].nunique()}"

nhom = df.groupby("Station Name")
ma_tran_day_du = pd.DataFrame({
    "C1_so_phien": nhom.size(),
    "C2_tong_dien_nang": nhom["energy_kwh"].sum(),
    "C3_dien_nang_moi_phien": nhom["energy_kwh"].mean(),
    "C4_gio_sac_moi_phien": nhom["charging_h"].mean(),
    "C5_ty_le_nhan_roi": nhom["idle_ratio"].mean(),
    "C6_ty_le_chiem_dung_nghiem_trong": nhom["chiem_dung_nghiem_trong"].mean(),
}).round(6)

X = ma_tran_day_du[ma_tran_day_du["C1_so_phien"] >= 500].sort_values("C1_so_phien", ascending=False).copy()
assert len(X) == 33, f"Expected 33 eligible stations, got {len(X)}"
assert int(X["C1_so_phien"].sum()) == 258681, f"Expected 258,681 sessions, got {int(X['C1_so_phien'].sum())}"

# Deterministic relation
diff_c2 = (X["C2_tong_dien_nang"] - X["C1_so_phien"] * X["C3_dien_nang_moi_phien"]).abs()
assert diff_c2.max() < 0.05, f"C2 = C1 * C3 violated: max diff {diff_c2.max()}"

# Correlation Plot
TIEU_CHI = {
    "C1_so_phien": ("Số phiên sạc", "phiên", +1),
    "C2_tong_dien_nang": ("Tổng điện năng", "kWh", +1),
    "C3_dien_nang_moi_phien": ("Điện năng bình quân mỗi phiên", "kWh/phiên", +1),
    "C4_gio_sac_moi_phien": ("Thời gian sạc hữu ích bình quân", "giờ/phiên", +1),
    "C5_ty_le_nhan_roi": ("Tỷ lệ chiếm dụng nhàn rỗi", "tỷ lệ", -1),
    "C6_ty_le_chiem_dung_nghiem_trong": ("Tỷ lệ phiên chiếm dụng nghiêm trọng", "tỷ lệ", -1),
}
ma_nhan = ["C1", "C2", "C3", "C4", "C5", "C6"]
ten_tieu_chi_ngan = ["C1: Số phiên", "C2: Tổng kWh", "C3: kWh/phiên", "C4: Giờ sạc/phiên", "C5: Tỷ lệ nhàn rỗi", "C6: Chiếm dụng nặng"]

corr_pearson = X[list(TIEU_CHI.keys())].corr(method="pearson")
fig, ax = plt.subplots(figsize=(6.5, 5), dpi=200)
sns.heatmap(corr_pearson, annot=True, fmt=".3f", cmap="vlag", vmin=-1, vmax=1, ax=ax,
            xticklabels=ten_tieu_chi_ngan, yticklabels=ten_tieu_chi_ngan, cbar_kws={'label': 'Hệ số tương quan Pearson'})
ax.set_title("Ma trận tương quan Pearson giữa 6 tiêu chí hiệu suất", fontsize=11, fontweight="bold", pad=10)
plt.xticks(rotation=30, ha="right", fontsize=8)
plt.yticks(fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "hinh_3_4_tuong_quan_tieu_chi.png", bbox_inches="tight")
plt.close(fig)

# Min-Max Normalization
def chuan_hoa_minmax(X, tieu_chi):
    R = pd.DataFrame(index=X.index, columns=X.columns, dtype=float)
    for cot in X.columns:
        gia_tri = X[cot].astype(float)
        nho_nhat, lon_nhat = gia_tri.min(), gia_tri.max()
        if lon_nhat == nho_nhat:
            R[cot] = 1.0
            continue
        do_rong = lon_nhat - nho_nhat
        if tieu_chi[cot][2] > 0:
            R[cot] = (gia_tri - nho_nhat) / do_rong
        else:
            R[cot] = (lon_nhat - gia_tri) / do_rong
    return R

R = chuan_hoa_minmax(X[list(TIEU_CHI.keys())], TIEU_CHI)

# Entropy Weights
def trong_so_entropy(R):
    m = len(R)
    he_so_k = 1.0 / np.log(m)
    ket_qua = []
    for cot in R.columns:
        p = R[cot].to_numpy(dtype=float)
        tong = p.sum()
        p = np.full(m, 1.0 / m) if tong == 0 else p / tong
        entropy = -he_so_k * np.sum(np.where(p > 0, p * np.log(np.where(p > 0, p, 1.0)), 0.0))
        ket_qua.append({"Tiêu chí": cot, "Entropy (e_j)": entropy, "Độ phân kỳ (d_j = 1 - e_j)": 1 - entropy})
    bang = pd.DataFrame(ket_qua).set_index("Tiêu chí")
    bang["Trọng số Entropy (w_j)"] = bang["Độ phân kỳ (d_j = 1 - e_j)"] / bang["Độ phân kỳ (d_j = 1 - e_j)"].sum()
    bang["Tên tiêu chí"] = [TIEU_CHI[c][0] for c in bang.index]
    return bang

bang_entropy = trong_so_entropy(R)
w_entropy = bang_entropy["Trọng số Entropy (w_j)"]
w_equal = pd.Series(1.0 / R.shape[1], index=R.columns, name="Trọng số đều (w_j)")

# TOPSIS
def tinh_topsis(R, w):
    V = R.multiply(w, axis=1)
    A_plus = V.max(axis=0)
    A_minus = V.min(axis=0)
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    total_d = D_plus + D_minus
    CC = np.where(total_d == 0, 0.5, D_minus / total_d)
    res = pd.DataFrame({
        "D_plus": D_plus,
        "D_minus": D_minus,
        "TOPSIS_Score": CC,
    }, index=R.index)
    res["Rank"] = res["TOPSIS_Score"].rank(ascending=False, method="min").astype(int)
    return res

top_entropy = tinh_topsis(R, w_entropy)
top_equal = tinh_topsis(R, w_equal)

df_rank = pd.DataFrame({
    "Station Name": X.index,
    "C1_so_phien": X["C1_so_phien"],
    "Score_Entropy": top_entropy["TOPSIS_Score"].round(6),
    "Rank_Entropy": top_entropy["Rank"],
    "Score_Equal": top_equal["TOPSIS_Score"].round(6),
    "Rank_Equal": top_equal["Rank"],
    "Rank_Diff": (top_entropy["Rank"] - top_equal["Rank"]).abs(),
}).sort_values("Rank_Entropy")

# Save outputs
X.to_csv(OUTPUT_DIR / "nv4_station_criteria.csv", encoding="utf-8-sig")

so_sanh_ts = bang_entropy[["Tên tiêu chí", "Entropy (e_j)", "Độ phân kỳ (d_j = 1 - e_j)", "Trọng số Entropy (w_j)"]].copy()
so_sanh_ts["Trọng số đều (w_j)"] = w_equal
so_sanh_ts["Chênh lệch (w_Entropy - w_Equal)"] = so_sanh_ts["Trọng số Entropy (w_j)"] - so_sanh_ts["Trọng số đều (w_j)"]
so_sanh_ts.to_csv(OUTPUT_DIR / "nv4_criteria_weights.csv", encoding="utf-8-sig")

df_rank.to_csv(OUTPUT_DIR / "nv4_topsis_rankings.csv", index=False, encoding="utf-8-sig")

# Figure A: Bar chart of TOPSIS Scores
df_plot = df_rank.sort_values("Score_Entropy", ascending=True)
ten_ngan_tram = [s.replace("PALO ALTO CA / ", "") for s in df_plot["Station Name"]]

fig, ax = plt.subplots(figsize=(8, 9), dpi=200)
y = np.arange(len(df_plot))
ax.barh(y - 0.18, df_plot["Score_Entropy"], height=0.35, label="Trọng số Entropy", color="#2b6cb0")
ax.barh(y + 0.18, df_plot["Score_Equal"], height=0.35, label="Trọng số đều (1/6)", color="#718096", alpha=0.8)
ax.set_yticks(y)
ax.set_yticklabels(ten_ngan_tram, fontsize=7.5)
ax.set_xlabel("Điểm số TOPSIS ($C_i$)", fontsize=9, fontweight="bold")
ax.set_title("Xếp hạng hiệu suất 33 trạm sạc theo điểm số TOPSIS", fontsize=11, fontweight="bold", pad=12)
ax.set_xlim(0, 0.85)
ax.legend(loc="lower right", frameon=True, fontsize=8.5)
fig.tight_layout()
fig.savefig(FIG_DIR / "hinh_3_7_diem_topsis.png", bbox_inches="tight")
plt.close(fig)

# Figure B: Ranking comparison (Slope chart)
fig, ax = plt.subplots(figsize=(7, 10), dpi=200)
for idx, row in df_rank.iterrows():
    r_ent = row["Rank_Entropy"]
    r_eq = row["Rank_Equal"]
    diff = row["Rank_Diff"]
    name = row["Station Name"].replace("PALO ALTO CA / ", "")
    
    color = "#2b6cb0" if diff < 5 else ("#e53e3e" if r_ent > r_eq else "#319795")
    lw = 1.2 if diff < 5 else 2.2
    
    ax.plot([0, 1], [r_ent, r_eq], marker="o", color=color, linewidth=lw, alpha=0.85)
    ax.text(-0.03, r_ent, f"{r_ent}. {name}", ha="right", va="center", fontsize=6.8, color="#2d3748")
    ax.text(1.03, r_eq, f"{r_eq}. {name}", ha="left", va="center", fontsize=6.8, color="#2d3748")

ax.set_xticks([0, 1])
ax.set_xticklabels(["Thứ hạng Entropy", "Thứ hạng Trọng số đều"], fontsize=9.5, fontweight="bold")
ax.set_ylim(34, 0)
ax.set_ylabel("Thứ hạng (1 = Tốt nhất)", fontsize=9, fontweight="bold")
ax.set_title("So sánh dịch chuyển thứ hạng trạm sạc giữa hai phương pháp gán trọng số", fontsize=11, fontweight="bold", pad=14)
ax.spines[["top", "right", "bottom"]].set_visible(False)
ax.grid(axis="y", linestyle=":", alpha=0.5)
fig.tight_layout()
fig.savefig(FIG_DIR / "hinh_3_8_so_sanh_thu_hang.png", bbox_inches="tight")
plt.close(fig)

# Figure C: Scatter plot Score_Entropy vs Score_Equal
fig, ax = plt.subplots(figsize=(6.5, 6), dpi=200)
ax.scatter(df_rank["Score_Entropy"], df_rank["Score_Equal"], color="#2b6cb0", edgecolors="white", s=65, zorder=3)
ax.plot([0.15, 0.75], [0.15, 0.75], 'r--', alpha=0.7, label="Đường cân bằng y = x", zorder=2)

# Annotate highlighted stations
highlight = ["HAMILTON #2", "WEBSTER #1", "TED THOMPSON #4", "TED THOMPSON #3", "TED THOMPSON #2", "CAMBRIDGE #1", "BRYANT #2", "MPL #2", "CAMBRIDGE #4"]
for idx, row in df_rank.iterrows():
    name = row["Station Name"].replace("PALO ALTO CA / ", "")
    if any(h in name for h in highlight):
        ax.annotate(name, (row["Score_Entropy"], row["Score_Equal"]),
                    textcoords="offset points", xytext=(5, 4), fontsize=6.5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3, ec="gray", lw=0.5))

ax.set_xlabel("Điểm TOPSIS (Trọng số Entropy)", fontsize=9, fontweight="bold")
ax.set_ylabel("Điểm TOPSIS (Trọng số đều)", fontsize=9, fontweight="bold")
ax.set_title("Tương quan điểm số TOPSIS giữa Trọng số Entropy và Trọng số đều", fontsize=10.5, fontweight="bold", pad=10)
ax.legend(frameon=True, fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "hinh_3_9_phan_tan_diem.png", bbox_inches="tight")
plt.close(fig)

# Sensitivity Analysis
from test_sensitivity import all_res, df_summary
df_summary.to_csv(OUTPUT_DIR / "nv4_sensitivity_analysis.csv", index=False, encoding="utf-8-sig")

# Sensitivity Figure
fig, ax = plt.subplots(figsize=(7.5, 4), dpi=200)
scen_names = [r["Scenario"].split(":")[0] for r in all_res if r["Scenario"] != "S0: Gốc (C1-C6)"]
spear_vals = [r["Spearman_Entropy"] for r in all_res if r["Scenario"] != "S0: Gốc (C1-C6)"]
kend_vals = [r["Kendall_Entropy"] for r in all_res if r["Scenario"] != "S0: Gốc (C1-C6)"]

x = np.arange(len(scen_names))
w = 0.35
ax.bar(x - w/2, spear_vals, width=w, label="Spearman Rank Corr", color="#2b6cb0")
ax.bar(x + w/2, kend_vals, width=w, label="Kendall Tau", color="#4fd1c5")

for i, v in enumerate(spear_vals):
    ax.text(i - w/2, v + 0.015, f"{v:.3f}", ha="center", fontsize=7)
for i, v in enumerate(kend_vals):
    ax.text(i + w/2, v + 0.015, f"{v:.3f}", ha="center", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(scen_names, fontsize=8)
ax.set_ylim(0.5, 1.08)
ax.set_ylabel("Hệ số tương quan thứ hạng so với S0", fontsize=8.5, fontweight="bold")
ax.set_title("Độ nhạy thứ hạng TOPSIS (Entropy) qua các kịch bản kiểm định", fontsize=10.5, fontweight="bold", pad=10)
ax.legend(frameon=True, fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "hinh_3_10_phan_tich_do_nhay.png", bbox_inches="tight")
plt.close(fig)

print("Generated all figures, tables and CSV outputs successfully!")

