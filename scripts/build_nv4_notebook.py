import json
import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

# Title
cells.append(nbf.v4.new_markdown_cell(
"""# NV4 — Đánh giá hiệu suất vận hành mạng lưới trạm sạc

**Học phần:** Phân tích Dữ liệu Kinh doanh (IS403)  
**Mục tiêu NV4:** Xây dựng ma trận tiêu chí hiệu suất cấp trạm sạc, xác định trọng số bằng phương pháp Entropy đối sánh với Trọng số đều, và áp dụng mô hình TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) dựa trên chuẩn hóa Min-Max để xếp hạng đa tiêu chí 33 trạm sạc công cộng tại thành phố Palo Alto.
"""
))

# Section 1
cells.append(nbf.v4.new_markdown_cell(
"""## 1. Khai báo thư viện, thiết lập cấu hình và tham số thực nghiệm

Phần này cấu hình môi trường thực thi, khai báo đường dẫn tương đối dự án (hỗ trợ thực thi từ thư mục gốc hoặc thư mục `notebooks/`), các hằng số kỹ thuật và nhãn hiển thị trực quan hóa."""
))

cells.append(nbf.v4.new_code_cell(
"""import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr, kendalltau

# Thiết lập hiển thị pandas
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", lambda v: f"{v:,.4f}")

# Cấu hình phong cách biểu đồ
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

# Thiết lập đường dẫn dự án linh hoạt
BASE_DIR = Path("..") if Path("../data").exists() else Path(".")
DUONG_DAN_CSV = BASE_DIR / "data" / "raw" / "EVChargingStationUsage.csv"
THU_MUC_XUAT = BASE_DIR / "outputs"
THU_MUC_HINH = THU_MUC_XUAT / "figures"

THU_MUC_XUAT.mkdir(parents=True, exist_ok=True)
THU_MUC_HINH.mkdir(parents=True, exist_ok=True)

# Tham số nghiệp vụ và kỹ thuật
NGUONG_PHIEN_TOI_THIEU = 500       # Ngưỡng tối thiểu để đưa vào ma trận xếp hạng trạm
TRAN_CONG_SUAT_L2_KW = 19.2       # Trần công suất vật lý trạm Level 2 (80A x 240V)
NGUONG_CHIEM_DUNG = 0.5           # Ngưỡng định nghĩa phiên chiếm dụng nhàn rỗi nghiêm trọng (> 50%)

TEN_NGAN = {
    "C1": "Số phiên", 
    "C2": "Tổng kWh", 
    "C3": "kWh/phiên",
    "C4": "Giờ sạc/phiên", 
    "C5": "Nhàn rỗi (đảo)", 
    "C6": "Chiếm dụng nặng (đảo)"
}

print(f"Đường dẫn dữ liệu: {DUONG_DAN_CSV.resolve()}")
print(f"Thư mục xuất kết quả: {THU_MUC_XUAT.resolve()}")
"""
))

# Section 2
cells.append(nbf.v4.new_markdown_cell(
r"""## 2. Nạp dữ liệu và kiểm soát chất lượng dữ liệu kế thừa từ NV1

Dữ liệu giao dịch được nạp từ tệp CSV thô và làm sạch theo quy chuẩn thống nhất từ Nhiệm vụ 1 (NV1):
1. **Loại bỏ trùng lặp hoàn toàn:** Xóa bỏ các bản ghi giao dịch trùng lặp 100%.
2. **Quy đổi thời lượng:** Chuyển đổi định dạng `hh:mm:ss` sang giây nguyên và giờ để đảm bảo độ chính xác tính toán.
3. **Kiểm tra tính logic thời gian:** Loại bỏ các phiên có tổng thời lượng $\le 0$, thời gian sạc $\le 0$, hoặc thời gian sạc vượt quá tổng thời lượng kết nối ($T_{\text{charging}} > T_{\text{total}}$).
4. **Kiểm tra trần công suất vật lý:** Loại các phiên có công suất sạc bình quân vượt trần vật lý trạm sạc Level 2 ($P_{\text{avg}} > 19,2\text{ kW}$).
5. **Kiểm tra độ lệch mốc thời gian:** Loại bỏ phiên có sai lệch giữa hiệu mốc thời gian ghi nhận (`End Date` - `Start Date`) và trường tổng thời lượng ghi nhận vượt quá 59 giây (dung sai ghi nhận cảm biến).
"""
))

cells.append(nbf.v4.new_code_cell(
"""def giay(s):
    try:
        h, m, gi = str(s).split(":")
        return int(h) * 3600 + int(m) * 60 + int(gi)
    except Exception:
        return np.nan

def doc_du_lieu(duong_dan):
    df = pd.read_csv(duong_dan, encoding="utf-8-sig", low_memory=False)
    df["total_s"] = df["Total Duration (hh:mm:ss)"].map(giay)
    df["charging_s"] = df["Charging Time (hh:mm:ss)"].map(giay)
    df["total_h"] = df["total_s"] / 3600
    df["charging_h"] = df["charging_s"] / 3600
    df["energy_kwh"] = pd.to_numeric(df["Energy (kWh)"], errors="coerce")
    return df

def lam_sach(df):
    nhat_ky = [("1. Bản ghi giao dịch thô ban đầu", len(df))]

    df = df.drop_duplicates()
    nhat_ky.append(("2. Sau khi loại bản ghi trùng lặp tuyệt đối", len(df)))

    hop_le_thoi_gian = (
        df["total_h"].gt(0) & df["charging_h"].gt(0) & df["charging_h"].le(df["total_h"])
    )
    df = df[hop_le_thoi_gian]
    nhat_ky.append(("3. Sau khi loại phiên sai logic thời gian", len(df)))

    df = df[(df["energy_kwh"] / df["charging_h"]).le(TRAN_CONG_SUAT_L2_KW)]
    nhat_ky.append(("4. Sau khi loại phiên vượt trần công suất Level 2 (19.2 kW)", len(df)))

    # Dung sai 59 giây: sai lệch từ 60 giây trở lên là lỗi ghi nhận mốc thời gian
    bat_dau = pd.to_datetime(df["Start Date"], errors="coerce")
    ket_thuc = pd.to_datetime(df["End Date"], errors="coerce")
    lech_giay = (df["total_s"] - (ket_thuc - bat_dau).dt.total_seconds()).abs()
    df = df[lech_giay.le(59)]
    nhat_ky.append(("5. Sau khi loại phiên lệch mốc thời gian từ 60 giây", len(df)))

    return df.copy(), pd.DataFrame(nhat_ky, columns=["Bước xử lý", "Số bản ghi"])

du_lieu_tho = doc_du_lieu(DUONG_DAN_CSV)
df, nhat_ky = lam_sach(du_lieu_tho)
nhat_ky["Tỷ lệ duy trì (%)"] = (nhat_ky["Số bản ghi"] / nhat_ky["Số bản ghi"].iloc[0] * 100).round(4)
display(nhat_ky)

# Kiểm tra xác nhận số phiên hợp lệ đạt đúng 258,720
assert len(df) == 258720, f"Kỳ vọng 258,720 phiên hợp lệ, thực tế nhận được {len(df):,}"
print(f"-> [XÁC NHẬN] Tập dữ liệu hợp lệ đạt đúng {len(df):,} phiên sạc.")
"""
))

# Section 3
cells.append(nbf.v4.new_markdown_cell(
r"""## 3. Chuẩn hóa danh xưng trạm sạc & Đặc trưng hành vi cấp phiên

- **Chuẩn hóa danh xưng trạm:** Trong dữ liệu gốc, `"BRYANT # 1"` là biến thể chính tả có dấu cách dư thừa của trạm `"BRYANT #1"`. Quy tắc chuẩn hóa xử lý đồng nhất về một tên duy nhất.
- **Thời gian nhàn rỗi ($T_{\text{idle}}$):** Khoảng thời gian phương tiện chiếm dụng cổng sạc sau khi đã ngừng nạp điện: $T_{\text{idle}} = T_{\text{total}} - T_{\text{charging}} \ge 0$.
- **Tỷ lệ nhàn rỗi (Idle Ratio):** Tỷ số giữa thời gian nhàn rỗi và tổng thời lượng kết nối: $\text{Idle Ratio} = T_{\text{idle}} / T_{\text{total}} \in [0, 1]$.
- **Cờ chiếm dụng nghiêm trọng:** Đánh dấu phiên có $\text{Idle Ratio} > 0,5$.
"""
))

cells.append(nbf.v4.new_code_cell(
r"""# Chuẩn hóa tên trạm
df["Station Name"] = (df["Station Name"].str.replace(r"\s+", " ", regex=True).str.strip()
                      .str.replace("BRYANT # 1", "BRYANT #1", regex=False))

df["idle_h"] = (df["total_h"] - df["charging_h"]).clip(lower=0)
df["idle_ratio"] = df["idle_h"] / df["total_h"]
df["chiem_dung_nghiem_trong"] = df["idle_ratio"].gt(NGUONG_CHIEM_DUNG).astype(int)

so_tram_tong = df["Station Name"].nunique()
print(f"Tổng số tên trạm sạc phân biệt sau chuẩn hóa: {so_tram_tong} trạm (Kỳ vọng: 46 trạm)")
assert so_tram_tong == 46, f"Kỳ vọng 46 trạm, thực tế: {so_tram_tong}"

display(df[["Station Name", "total_h", "charging_h", "idle_h", "idle_ratio", "energy_kwh"]].head())
"""
))

# Section 4
cells.append(nbf.v4.new_markdown_cell(
r"""## 4. Xây dựng ma trận tiêu chí cấp trạm sạc ($X$) & Kiểm định ngưỡng chọn mẫu

### 4.1. Định nghĩa 6 tiêu chí hiệu suất vận hành (C1–C6)

Ma trận quyết định ban đầu $X$ có $m$ hàng (trạm sạc) và $n=6$ cột tiêu chí bao quát 4 khía cạnh vận hành:
1. **$C_1$ — Số phiên sạc (phiên, Lợi ích +1):** Đo lường quy mô nhu cầu và lưu lượng phục vụ của trạm.
2. **$C_2$ — Tổng điện năng cung ứng (kWh, Lợi ích +1):** Đo lường tổng sản lượng điện truyền tải vào mạng lưới phương tiện.
3. **$C_3$ — Điện năng bình quân mỗi phiên (kWh/phiên, Lợi ích +1):** Đo lường cường độ nhu cầu sạc trên từng giao dịch.
4. **$C_4$ — Thời gian sạc hữu ích bình quân (giờ/phiên, Lợi ích +1):** Thời gian thực tế nạp dòng vào pin.
5. **$C_5$ — Tỷ lệ thời gian nhàn rỗi bình quân (tỷ lệ, Chi phí -1):** Mức độ đỗ xe ngâm trụ trung bình trên mỗi phiên sạc.
6. **$C_6$ — Tỷ lệ phiên chiếm dụng nghiêm trọng (tỷ lệ, Chi phí -1):** Tần suất phát sinh các phiên đỗ ngâm nhàn rỗi vượt quá 50% thời gian cắm cáp.

### 4.2. Biện giải ngưỡng chọn mẫu 500 phiên
Phân tích phân bố số phiên theo trạm cho thấy khoảng trống phân vị tự nhiên rất lớn:
- 13 trạm sạc ngoại vi chỉ có từ 1 đến 8 phiên sạc trong toàn bộ giai đoạn (tổng cộng chỉ có 39 phiên). Các trạm này là trạm thử nghiệm hoặc ngừng hoạt động sớm, giá trị trung bình thống kê không có độ tin cậy.
- 33 trạm sạc còn lại đều có từ 1.043 phiên sạc trở lên.
- Ngưỡng 500 phiên nằm hoàn toàn trong khoảng trống $[8, 1.043]$ phiên. Do đó, bất kỳ ngưỡng nào trong đoạn này đều giữ lại đúng **33 trạm sạc hợp lệ**, đại diện cho **258.681 phiên sạc (chiếm 99,985% tổng dữ liệu)**.
"""
))

cells.append(nbf.v4.new_code_cell(
"""TIEU_CHI = {
    "C1_so_phien": ("Số phiên sạc", "phiên", +1),
    "C2_tong_dien_nang": ("Tổng điện năng", "kWh", +1),
    "C3_dien_nang_moi_phien": ("Điện năng bình quân mỗi phiên", "kWh/phiên", +1),
    "C4_gio_sac_moi_phien": ("Thời gian sạc hữu ích bình quân", "giờ/phiên", +1),
    "C5_ty_le_nhan_roi": ("Tỷ lệ chiếm dụng nhàn rỗi", "tỷ lệ", -1),
    "C6_ty_le_chiem_dung_nghiem_trong": ("Tỷ lệ phiên chiếm dụng nghiêm trọng", "tỷ lệ", -1),
}

nhom = df.groupby("Station Name")
ma_tran_day_du = pd.DataFrame({
    "C1_so_phien": nhom.size(),
    "C2_tong_dien_nang": nhom["energy_kwh"].sum(),
    "C3_dien_nang_moi_phien": nhom["energy_kwh"].mean(),
    "C4_gio_sac_moi_phien": nhom["charging_h"].mean(),
    "C5_ty_le_nhan_roi": nhom["idle_ratio"].mean(),
    "C6_ty_le_chiem_dung_nghiem_trong": nhom["chiem_dung_nghiem_trong"].mean(),
}).round(6)

X = (ma_tran_day_du[ma_tran_day_du["C1_so_phien"] >= NGUONG_PHIEN_TOI_THIEU]
     .sort_values("C1_so_phien", ascending=False)).copy()

# Thêm biến chẩn đoán C5_weighted (tỷ lệ thời gian nhàn rỗi theo tổng thời lượng cắm cáp)
c5_weighted = nhom["idle_h"].sum() / nhom["total_h"].sum()
X["C5_weighted"] = c5_weighted.loc[X.index].round(6)

duoi_nguong = ma_tran_day_du.loc[ma_tran_day_du["C1_so_phien"] < NGUONG_PHIEN_TOI_THIEU, "C1_so_phien"]
tren_nguong = ma_tran_day_du.loc[ma_tran_day_du["C1_so_phien"] >= NGUONG_PHIEN_TOI_THIEU, "C1_so_phien"]

print(f"Số lượng trạm trong ma trận chính thức: {len(X)} trạm (Kỳ vọng: 33 trạm)")
print(f"Tổng số phiên trong ma trận: {int(X['C1_so_phien'].sum()):,} / {len(df):,} phiên ({X['C1_so_phien'].sum()/len(df)*100:.3f}%)")
print(f"Khoảng trống phân vị ngưỡng: Max nhóm bị loại = {int(duoi_nguong.max())} phiên -> Min nhóm được chọn = {int(tren_nguong.min()):,} phiên")

assert len(X) == 33
assert int(X['C1_so_phien'].sum()) == 258681

display(X[list(TIEU_CHI.keys())].head(10))
"""
))

# Section 5
cells.append(nbf.v4.new_markdown_cell(
r"""### 4.3. Kiểm định quan hệ đại số xác định ($C_2 = C_1 \times C_3$) & Phân tích tương quan tiêu chí

1. **Quan hệ đại số xác định giữa C1, C2 và C3:**
   Về mặt định nghĩa toán học:
   $$C_2 = \sum_{i=1}^{C_1} E_i = C_1 \times \left(\frac{1}{C_1} \sum_{i=1}^{C_1} E_i\right) = C_1 \times C_3$$
   Kiểm tra thực nghiệm trên ma trận $X$ cho thấy sai lệch tuyệt đối cực đại giữa $C_2$ và tích $C_1 \times C_3$ là **$0,0095\text{ kWh}$** (hoàn toàn do sai số làm tròn dấu phẩy động).
   *Hàm ý phương pháp luận:* C2 phụ thuộc xác định vào C1 và C3. Trong mô hình thực nghiệm, C1 đại diện cho quy mô lưu lượng giao dịch (*transaction volume*), C2 đại diện cho tổng công suất năng lượng lưới phải đáp ứng (*grid energy scale*), và C3 đại diện cho dung lượng nạp trung bình mỗi lượt (*vehicle battery capacity demand*). Mối quan hệ này sẽ được đánh giá độ nhạy chuyên sâu tại Kịch bản S1 và S2 (loại bỏ C2 hoặc C1).

2. **Phân tích tương quan Pearson & Spearman:**
   - Cặp $(C_1, C_2)$ có tương quan cực cao ($r = 0,9815$; $\rho = 0,9863$), xác nhận sự chi phối mạnh mẽ của quy mô giao dịch đến tổng năng lượng.
   - Cặp $(C_5, C_6)$ có tương quan rất cao ($r = 0,9852$; $\rho = 0,9719$), cho thấy trạm có tỷ lệ nhàn rỗi bình quân cao cũng là trạm có tỷ lệ phiên ngâm trụ nghiêm trọng cao. Kịch bản S3 sẽ kiểm tra độ dư thừa khi loại bỏ C6.
   - Cặp $(C_3, C_4)$ có tương quan thuận rõ nét ($r = 0,7380$; $\rho = 0,6922$), phù hợp với nguyên lý vật lý sạc Level 2 với công suất nạp tương đối đồng đều.
"""
))

cells.append(nbf.v4.new_code_cell(
"""# Kiểm tra sai lệch đại số xác định C2 = C1 * C3
sai_lech_c2 = (X["C2_tong_dien_nang"] - X["C1_so_phien"] * X["C3_dien_nang_moi_phien"]).abs()
print(f"Sai lệch tuyệt đối lớn nhất |C2 - C1 * C3|: {sai_lech_c2.max():.6f} kWh")
assert sai_lech_c2.max() < 0.05, "Vi phạm đẳng thức toán học C2 = C1 * C3"

# Tính toán ma trận tương quan Pearson và Spearman
cols_tieu_chi = list(TIEU_CHI.keys())
corr_p = X[cols_tieu_chi].corr(method="pearson")
corr_s = X[cols_tieu_chi].corr(method="spearman")

print("=== MA TRẬN TƯƠNG QUAN PEARSON ===")
display(corr_p.round(4))

# Trực quan hóa Heatmap tương quan
ten_rut_gon = [f"{k[:2]}: {TEN_NGAN[k[:2]]}" for k in ["C1", "C2", "C3", "C4", "C5", "C6"]]
fig, ax = plt.subplots(figsize=(6.8, 5.2), dpi=200)
sns.heatmap(corr_p, annot=True, fmt=".3f", cmap="vlag", vmin=-1, vmax=1, ax=ax,
            xticklabels=ten_rut_gon, yticklabels=ten_rut_gon, cbar_kws={'label': 'Hệ số tương quan Pearson'})
ax.set_title("Hình 3.4 — Ma trận tương quan Pearson giữa 6 tiêu chí hiệu suất", fontsize=10.5, fontweight="bold", pad=12)
plt.xticks(rotation=25, ha="right", fontsize=8)
plt.yticks(fontsize=8)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_4_tuong_quan_tieu_chi.png", bbox_inches="tight")
plt.show()
"""
))

# Section 6
cells.append(nbf.v4.new_markdown_cell(
r"""## 5. Chuẩn hóa Min-Max định hướng mục tiêu (Direction-Aware Min-Max Normalization)

Các tiêu chí có đơn vị đo lường và thang giá trị vật lý khác biệt (phiên, kWh, giờ, tỷ lệ). Phép chuẩn hóa Min-Max đưa toàn bộ các cột về đoạn $[0, 1]$ đồng thời **đồng nhất hướng lợi ích (+1)**:
- Với tiêu chí lợi ích ($C_1, C_2, C_3, C_4$): Giá trị lớn nhất nhận 1 (tốt nhất), nhỏ nhất nhận 0.
  $$R_{ij} = \frac{X_{ij} - \min_i X_{ij}}{\max_i X_{ij} - \min_i X_{ij}}$$
- Với tiêu chí chi phí ($C_5, C_6$): Giá trị nhỏ nhất nhận 1 (tốt nhất - ít chiếm dụng nhất), lớn nhất nhận 0.
  $$R_{ij} = \frac{\max_i X_{ij} - X_{ij}}{\max_i X_{ij} - \min_i X_{ij}}$$

*Ý nghĩa then chốt:* Trong ma trận chuẩn hóa $R$, mọi giá trị $R_{ij} \in [0, 1]$ đều thể hiện mức độ xuất sắc (1 là tốt nhất, 0 là kém nhất).
"""
))

cells.append(nbf.v4.new_code_cell(
"""def chuan_hoa_minmax(X_mat, tieu_chi_dict):
    R_mat = pd.DataFrame(index=X_mat.index, columns=X_mat.columns, dtype=float)
    for cot in X_mat.columns:
        gia_tri = X_mat[cot].astype(float)
        nho_nhat, lon_nhat = gia_tri.min(), gia_tri.max()
        if lon_nhat == nho_nhat:
            R_mat[cot] = 1.0
            continue
        do_rong = lon_nhat - nho_nhat
        if tieu_chi_dict[cot][2] > 0:
            R_mat[cot] = (gia_tri - nho_nhat) / do_rong
        else:
            R_mat[cot] = (lon_nhat - gia_tri) / do_rong
    return R_mat

R = chuan_hoa_minmax(X[list(TIEU_CHI.keys())], TIEU_CHI)

# Kiểm tra tính toàn vẹn ma trận chuẩn hóa
assert R.isna().sum().sum() == 0, "Ma trận R chứa giá trị thiếu (NaN)"
assert (R.min().min() >= 0.0) and (R.max().max() <= 1.0), "Khoảng giá trị R vi phạm đoạn [0, 1]"
print(f"Khoảng giá trị ma trận R: [{R.to_numpy().min():.4f}, {R.to_numpy().max():.4f}]")
display(R.head(8))

# Trực quan hóa Heatmap ma trận R
ma_nhan = [c.split("_")[0] for c in R.columns]
ten_tram = [s.replace("PALO ALTO CA / ", "") for s in R.index]

fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=200)
im = ax.imshow(R.values.T, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
ax.set_yticks(range(len(R.columns)))
ax.set_yticklabels([f"{a}. {TEN_NGAN[a]}" for a in ma_nhan], fontsize=7)
ax.set_xticks(range(len(ten_tram)))
ax.set_xticklabels(ten_tram, rotation=90, fontsize=5.5)
ax.set_xlabel("33 trạm sạc, sắp xếp giảm dần theo số phiên (C1)", fontsize=7.5)
cb = fig.colorbar(im, ax=ax, pad=0.01)
cb.set_label("Giá trị chuẩn hóa Min-Max (1 = tốt nhất)", fontsize=7)
cb.ax.tick_params(labelsize=6)
ax.tick_params(length=0)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_5_ma_tran_chuan_hoa.png", bbox_inches="tight")
plt.show()
"""
))

# Section 7
cells.append(nbf.v4.new_markdown_cell(
r"""## 6. Xác định trọng số tiêu chí: Phương pháp Entropy đối chiếu Trọng số đều

### 6.1. Trọng số Entropy thông tin (Entropy Weighting Method)
Phương pháp Entropy đo lường mức độ biến thiên khách quan của dữ liệu: tiêu chí nào có độ phân tán càng cao giữa các trạm thì khả năng mang thông tin phân biệt càng lớn và nhận trọng số $w_j$ càng cao.
1. Tính tỷ trọng: $p_{ij} = R_{ij} / \sum_{i=1}^m R_{ij}$ (quy ước $0 \times \ln(0) = 0$).
2. Tính chỉ số Entropy: $e_j = -\frac{1}{\ln(m)} \sum_{i=1}^m p_{ij} \ln(p_{ij})$.
3. Tính độ phân kỳ thông tin: $d_j = 1 - e_j$.
4. Chuẩn hóa trọng số: $w_j = d_j / \sum_{j=1}^n d_j$.

### 6.2. Trọng số đều (Equal Weighting - Benchmark)
Gán trọng số cân bằng tuyệt đối cho mọi tiêu chí: $w_j = 1/n = 1/6 \approx 0,1667$. Đây là kịch bản đối chứng giả định nhà quản trị coi trọng bình đẳng cả 4 khía cạnh vận hành.
"""
))

cells.append(nbf.v4.new_code_cell(
r"""def trong_so_entropy(R_mat, tieu_chi_dict=None):
    m = len(R_mat)
    he_so_k = 1.0 / np.log(m)
    ket_qua = []

    if tieu_chi_dict is None:
        tieu_chi_dict = TIEU_CHI

    for cot in R_mat.columns:
        p = R_mat[cot].to_numpy(dtype=float)
        tong = p.sum()
        p = np.full(m, 1.0 / m) if tong == 0 else p / tong
        entropy = -he_so_k * np.sum(np.where(p > 0, p * np.log(np.where(p > 0, p, 1.0)), 0.0))
        ket_qua.append({"Tiêu chí": cot, "Entropy (e_j)": entropy, "Độ phân kỳ (d_j = 1 - e_j)": 1 - entropy})

    bang = pd.DataFrame(ket_qua).set_index("Tiêu chí")
    bang["Trọng số Entropy (w_j)"] = bang["Độ phân kỳ (d_j = 1 - e_j)"] / bang["Độ phân kỳ (d_j = 1 - e_j)"].sum()
    bang["Tên tiêu chí"] = [tieu_chi_dict[c][0] if c in tieu_chi_dict else c for c in bang.index]
    return bang

bang_entropy = trong_so_entropy(R)
w_entropy = bang_entropy["Trọng số Entropy (w_j)"]
w_equal = pd.Series(1.0 / R.shape[1], index=R.columns, name="Trọng số đều (w_j)")

# So sánh hai bộ trọng số
so_sanh = bang_entropy[["Tên tiêu chí", "Entropy (e_j)", "Độ phân kỳ (d_j = 1 - e_j)", "Trọng số Entropy (w_j)"]].copy()
so_sanh["Trọng số đều (w_j)"] = w_equal
so_sanh["Chênh lệch"] = so_sanh["Trọng số Entropy (w_j)"] - so_sanh["Trọng số đều (w_j)"]
so_sanh["Tỷ lệ so với trọng số đều"] = so_sanh["Trọng số Entropy (w_j)"] * len(R.columns)
display(so_sanh.round(6))

# Trực quan hóa so sánh trọng số
x = np.arange(len(bang_entropy))
w = 0.38
deu = np.full(len(bang_entropy), 1 / len(bang_entropy))

fig, ax = plt.subplots(figsize=(6.8, 3.4), dpi=200)
ax.bar(x - w / 2, bang_entropy["Trọng số Entropy (w_j)"], w, label="Trọng số Entropy", color="#2b6cb0")
ax.bar(x + w / 2, deu, w, label="Trọng số đều (1/6)", color="#cbd5e0")
for i, v in enumerate(bang_entropy["Trọng số Entropy (w_j)"]):
    ax.text(i - w / 2, v + 0.006, f"{v:.4f}".replace(".", ","), ha="center", fontsize=6.5)
ax.set_xticks(x)
nhan_truc_x = [a + "\\n" + TEN_NGAN[a] for a in ma_nhan]
ax.set_xticklabels(nhan_truc_x, fontsize=7)
ax.set_ylabel("Trọng số", fontsize=8)
ax.set_ylim(0, 0.35)
ax.legend(fontsize=7.5, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(labelsize=7.5)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_6_trong_so.png", bbox_inches="tight")
plt.show()
"""
))

# Section 8
cells.append(nbf.v4.new_markdown_cell(
r"""## 7. Quy trình xếp hạng đa tiêu chí TOPSIS (Min-Max-based TOPSIS)

### 7.1. Thuật toán TOPSIS trên ma trận đã chuẩn hóa Min-Max
Do ma trận $R$ đã được chuẩn hóa định hướng lợi ích ($1$ luôn là phương án tối ưu, $0$ luôn là kém nhất cho cả 6 tiêu chí), quy trình TOPSIS gồm 5 bước tiêu chuẩn:
1. **Xây dựng ma trận quyết định có trọng số:**
   $$V_{ij} = w_j \times R_{ij}$$
2. **Xác định nghiệm lý tưởng dương ($A^+$) và nghiệm lý tưởng âm ($A^-$):**
   $$A_j^+ = \max_{i} V_{ij}, \quad A_j^- = \min_{i} V_{ij}$$
3. **Tính khoảng cách Euclid tới các nghiệm lý tưởng:**
   $$D_i^+ = \sqrt{\sum_{j=1}^n (V_{ij} - A_j^+)^2}, \quad D_i^- = \sqrt{\sum_{j=1}^n (V_{ij} - A_j^-)^2}$$
4. **Xác định hệ số gần nghiệm lý tưởng (Closeness Coefficient):**
   $$CC_i = \frac{D_i^-}{D_i^+ + D_i^-} \in [0, 1]$$
   *$CC_i$ càng cao thì trạm sạc càng gần nghiệm lý tưởng và càng xa nghiệm âm.*
5. **Xếp hạng trạm sạc:** Sắp xếp trạm sạc theo thứ tự $CC_i$ giảm dần.
"""
))

cells.append(nbf.v4.new_code_cell(
"""def tinh_topsis(R_mat, w_vec):
    # Bước 1: Ma trận chuẩn hóa có trọng số V
    V = R_mat.multiply(w_vec, axis=1)
    
    # Bước 2: Nghiệm lý tưởng dương và âm (toàn bộ cột trong R đều có hướng lợi ích)
    A_plus = V.max(axis=0)
    A_minus = V.min(axis=0)
    
    # Bước 3: Khoảng cách phân tách Euclid
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    
    # Bước 4: Hệ số tương đối CC_i
    total_d = D_plus + D_minus
    CC = np.where(total_d == 0, 0.5, D_minus / total_d)
    
    res = pd.DataFrame({
        "D_plus": D_plus,
        "D_minus": D_minus,
        "TOPSIS_Score": CC,
    }, index=R_mat.index)
    res["Rank"] = res["TOPSIS_Score"].rank(ascending=False, method="min").astype(int)
    return res

# Thực hiện xếp hạng theo Entropy và Equal Weighting
top_entropy = tinh_topsis(R, w_entropy)
top_equal = tinh_topsis(R, w_equal)

# Tổng hợp bảng thứ hạng hoàn chỉnh (Bảng A)
df_rank = pd.DataFrame({
    "Station Name": X.index,
    "C1_so_phien": X["C1_so_phien"],
    "Score_Entropy": top_entropy["TOPSIS_Score"].round(6),
    "Rank_Entropy": top_entropy["Rank"],
    "Score_Equal": top_equal["TOPSIS_Score"].round(6),
    "Rank_Equal": top_equal["Rank"],
    "Rank_Diff": (top_entropy["Rank"] - top_equal["Rank"]).abs(),
}).sort_values("Rank_Entropy").reset_index(drop=True)

print("=== BẢNG A: KẾT QUẢ XẾP HẠNG TOPSIS HOÀN CHỈNH CHO 33 TRẠM SẠC ===")
display(df_rank)

# Bảng B: Top 5 và Bottom 5 trạm sạc
print("\\n=== BẢNG B1: TOP 5 TRẠM XẾP THEO TRỌNG SỐ ENTROPY ===")
display(df_rank.head(5)[["Station Name", "C1_so_phien", "Score_Entropy", "Rank_Entropy", "Score_Equal", "Rank_Equal", "Rank_Diff"]])

print("\\n=== BẢNG B2: BOTTOM 5 TRẠM XẾP THEO TRỌNG SỐ ENTROPY ===")
display(df_rank.tail(5)[["Station Name", "C1_so_phien", "Score_Entropy", "Rank_Entropy", "Score_Equal", "Rank_Equal", "Rank_Diff"]])
"""
))

# Section 9
cells.append(nbf.v4.new_markdown_cell(
"""### 7.2. Trực quan hóa kết quả xếp hạng TOPSIS (Hình A, B, C)"""
))

cells.append(nbf.v4.new_code_cell(
"""# Hình A: Biểu đồ thanh ngang điểm số TOPSIS của 33 trạm sạc
df_plot = df_rank.sort_values("Score_Entropy", ascending=True)
ten_ngan_tram = [s.replace("PALO ALTO CA / ", "") for s in df_plot["Station Name"]]

fig, ax = plt.subplots(figsize=(8.2, 9.5), dpi=200)
y = np.arange(len(df_plot))
ax.barh(y - 0.18, df_plot["Score_Entropy"], height=0.35, label="Trọng số Entropy", color="#2b6cb0")
ax.barh(y + 0.18, df_plot["Score_Equal"], height=0.35, label="Trọng số đều (1/6)", color="#718096", alpha=0.8)
ax.set_yticks(y)
ax.set_yticklabels(ten_ngan_tram, fontsize=7.5)
ax.set_xlabel("Điểm số TOPSIS ($C_i$)", fontsize=9, fontweight="bold")
ax.set_title("Hình 3.7 — Xếp hạng hiệu suất 33 trạm sạc theo điểm số TOPSIS", fontsize=11, fontweight="bold", pad=12)
ax.set_xlim(0, 0.85)
ax.legend(loc="lower right", frameon=True, fontsize=8.5)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_7_diem_topsis.png", bbox_inches="tight")
plt.show()

# Hình B: Slope Chart so sánh thứ hạng giữa Entropy và Trọng số đều
fig, ax = plt.subplots(figsize=(7.2, 10.5), dpi=200)
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
ax.set_title("Hình 3.8 — So sánh dịch chuyển thứ hạng trạm sạc giữa hai phương pháp gán trọng số", fontsize=11, fontweight="bold", pad=14)
ax.spines[["top", "right", "bottom"]].set_visible(False)
ax.grid(axis="y", linestyle=":", alpha=0.5)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_8_so_sanh_thu_hang.png", bbox_inches="tight")
plt.show()

# Hình C: Đồ thị phân tán Score_Entropy vs Score_Equal
fig, ax = plt.subplots(figsize=(6.8, 6.2), dpi=200)
ax.scatter(df_rank["Score_Entropy"], df_rank["Score_Equal"], color="#2b6cb0", edgecolors="white", s=65, zorder=3)
ax.plot([0.15, 0.75], [0.15, 0.75], 'r--', alpha=0.7, label="Đường cân bằng y = x", zorder=2)

# Chú thích các trạm có độ lệch thứ hạng lớn
highlight = ["HAMILTON #2", "WEBSTER #1", "TED THOMPSON #4", "TED THOMPSON #3", "TED THOMPSON #2", "CAMBRIDGE #1", "BRYANT #2", "MPL #2", "CAMBRIDGE #4"]
for idx, row in df_rank.iterrows():
    name = row["Station Name"].replace("PALO ALTO CA / ", "")
    if any(h in name for h in highlight):
        ax.annotate(name, (row["Score_Entropy"], row["Score_Equal"]),
                    textcoords="offset points", xytext=(5, 4), fontsize=6.8,
                    bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.25, ec="gray", lw=0.5))

ax.set_xlabel("Điểm TOPSIS (Trọng số Entropy)", fontsize=9, fontweight="bold")
ax.set_ylabel("Điểm TOPSIS (Trọng số đều)", fontsize=9, fontweight="bold")
ax.set_title("Hình 3.9 — Tương quan điểm số TOPSIS giữa Trọng số Entropy và Trọng số đều", fontsize=10.5, fontweight="bold", pad=10)
ax.legend(frameon=True, fontsize=8)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_9_phan_tan_diem.png", bbox_inches="tight")
plt.show()
"""
))

# Section 10
cells.append(nbf.v4.new_markdown_cell(
r"""## 8. Phân tích độ ổn định thứ hạng và kiểm định độ nhạy (Sensitivity Analysis)

### 8.1. Đánh giá độ đồng thuận cơ sở giữa Entropy và Trọng số đều
Đo lường mức độ tương đồng giữa hai bộ thứ hạng cơ sở trên mô hình đầy đủ S0:
- Hệ số tương quan hạng Spearman: $\rho = 0,8185$ (tương quan thuận mạnh).
- Hệ số Kendall Tau: $\tau = 0,6288$.
- Độ trùng khớp nhóm Top 5: $3/5$ trạm (HAMILTON #2, WEBSTER #1, WEBSTER #2).
- Độ lệch thứ hạng bình quân: $4,30$ bậc.
- Độ lệch thứ hạng cực đại: $14$ bậc (trạm `TED THOMPSON #4`).
- Số trạm dịch chuyển $\ge 5$ bậc: $14/33$ trạm ($42,4\%$).

*Nhận định nghiệp vụ:* Tương quan thứ hạng cao không đồng nghĩa với việc hai phương pháp dẫn đến kết luận vận hành giống nhau. Trọng số Entropy dồn $57,1\%$ trọng số vào hai biến quy mô $C_1$ và $C_2$, tạo ưu thế vượt trội cho các cụm trạm lớn. Trong khi đó, Trọng số đều cân bằng đều 4 khía cạnh, tôn vinh các trạm có hiệu suất phiên sạc cao và ít chiếm dụng nhàn rỗi.

### 8.2. Thiết lập 6 kịch bản kiểm định độ nhạy (Sensitivity Scenarios)
1. **Kịch bản S0 (Mô hình gốc):** 6 tiêu chí C1–C6.
2. **Kịch bản S1 (Loại C2 — Tổng điện năng):** Đánh giá tác động khi loại bỏ biến có quan hệ đại số xác định $C_2 = C_1 \times C_3$.
3. **Kịch bản S2 (Loại C1 — Số phiên sạc):** Đánh giá tác động khi loại bỏ biến quy mô lưu lượng giao dịch.
4. **Kịch bản S3 (Loại C6 — Tỷ lệ chiếm dụng nghiêm trọng):** Đánh giá mức độ dư thừa thông tin giữa $C_5$ và $C_6$.
5. **Kịch bản S4 (Loại C4 — Thời gian sạc hữu ích):** Đánh giá tác động của biến thời lượng sạc có hướng tác động phụ thuộc bối cảnh.
6. **Kịch bản S5 (Thay $C_5$ bằng $C_5$ trọng số thời lượng):** Thay thế tỷ lệ nhàn rỗi trung bình phiên bằng tỷ trọng thời gian nhàn rỗi trên tổng thời lượng cắm cáp ($\sum T_{\text{idle}} / \sum T_{\text{total}}$).
7. **Kịch bản S6 (Chuẩn hóa vector cổ điển):** Đối sánh phương pháp Min-Max TOPSIS với TOPSIS chuẩn hóa vector kinh điển.
"""
))

cells.append(nbf.v4.new_code_cell(
"""# Hàm đánh giá kịch bản
def evaluate_scenario(name, X_scen, tieu_chi_scen, s0_ranks_ent, s0_ranks_eq):
    R_scen = chuan_hoa_minmax(X_scen, tieu_chi_scen)
    w_ent = trong_so_entropy(R_scen, tieu_chi_scen)["Trọng số Entropy (w_j)"]
    w_eq = pd.Series(1.0 / R_scen.shape[1], index=R_scen.columns)
    
    top_ent = tinh_topsis(R_scen, w_ent)
    top_eq = tinh_topsis(R_scen, w_eq)
    
    # So sánh với S0 Entropy
    spear_ent, _ = spearmanr(top_ent["Rank"], s0_ranks_ent)
    tau_ent, _ = kendalltau(top_ent["Rank"], s0_ranks_ent)
    rank_diff_ent = (top_ent["Rank"] - s0_ranks_ent).abs()
    top5_ent = set(top_ent.sort_values("Rank").head(5).index)
    top5_s0_ent = set(s0_ranks_ent.sort_values().head(5).index)
    overlap_ent = len(top5_ent.intersection(top5_s0_ent))
    
    # So sánh với S0 Equal
    spear_eq, _ = spearmanr(top_eq["Rank"], s0_ranks_eq)
    tau_eq, _ = kendalltau(top_eq["Rank"], s0_ranks_eq)
    rank_diff_eq = (top_eq["Rank"] - s0_ranks_eq).abs()
    top5_eq = set(top_eq.sort_values("Rank").head(5).index)
    top5_s0_eq = set(s0_ranks_eq.sort_values().head(5).index)
    overlap_eq = len(top5_eq.intersection(top5_s0_eq))
    
    return {
        "Scenario": name,
        "Criteria_Count": len(tieu_chi_scen),
        "Spearman_Entropy": round(spear_ent, 4),
        "Kendall_Entropy": round(tau_ent, 4),
        "Mean_Rank_Diff_Entropy": round(rank_diff_ent.mean(), 2),
        "Max_Rank_Diff_Entropy": int(rank_diff_ent.max()),
        "Stations_Diff_ge5_Entropy": int((rank_diff_ent >= 5).sum()),
        "Top5_Overlap_Entropy": f"{overlap_ent}/5",
        "Spearman_Equal": round(spear_eq, 4),
        "Kendall_Equal": round(tau_eq, 4),
        "Mean_Rank_Diff_Equal": round(rank_diff_eq.mean(), 2),
        "Max_Rank_Diff_Equal": int(rank_diff_eq.max()),
        "Stations_Diff_ge5_Equal": int((rank_diff_eq >= 5).sum()),
        "Top5_Overlap_Equal": f"{overlap_eq}/5",
        "top_ent_df": top_ent,
        "top_eq_df": top_eq,
    }

s0_ranks_entropy = top_entropy["Rank"]
s0_ranks_equal = top_equal["Rank"]

# S0
res_s0 = evaluate_scenario("S0: Gốc (C1-C6)", X[list(TIEU_CHI.keys())], TIEU_CHI, s0_ranks_entropy, s0_ranks_equal)

# S1: Loại C2
cols_s1 = [c for c in TIEU_CHI.keys() if c != "C2_tong_dien_nang"]
res_s1 = evaluate_scenario("S1: Loại C2 (Tổng kWh)", X[cols_s1], {c: TIEU_CHI[c] for c in cols_s1}, s0_ranks_entropy, s0_ranks_equal)

# S2: Loại C1
cols_s2 = [c for c in TIEU_CHI.keys() if c != "C1_so_phien"]
res_s2 = evaluate_scenario("S2: Loại C1 (Số phiên)", X[cols_s2], {c: TIEU_CHI[c] for c in cols_s2}, s0_ranks_entropy, s0_ranks_equal)

# S3: Loại C6
cols_s3 = [c for c in TIEU_CHI.keys() if c != "C6_ty_le_chiem_dung_nghiem_trong"]
res_s3 = evaluate_scenario("S3: Loại C6 (Chiếm dụng nặng)", X[cols_s3], {c: TIEU_CHI[c] for c in cols_s3}, s0_ranks_entropy, s0_ranks_equal)

# S4: Loại C4
cols_s4 = [c for c in TIEU_CHI.keys() if c != "C4_gio_sac_moi_phien"]
res_s4 = evaluate_scenario("S4: Loại C4 (Thời gian sạc)", X[cols_s4], {c: TIEU_CHI[c] for c in cols_s4}, s0_ranks_entropy, s0_ranks_equal)

# S5: Thay C5 bằng C5_weighted
tc_s5 = TIEU_CHI.copy()
tc_s5.pop("C5_ty_le_nhan_roi")
tc_s5["C5_weighted"] = ("Tỷ lệ thời gian nhàn rỗi trọng số", "tỷ lệ", -1)
cols_s5 = ["C1_so_phien", "C2_tong_dien_nang", "C3_dien_nang_moi_phien", "C4_gio_sac_moi_phien", "C5_weighted", "C6_ty_le_chiem_dung_nghiem_trong"]
res_s5 = evaluate_scenario("S5: C5 trọng số thời lượng", X[cols_s5], tc_s5, s0_ranks_entropy, s0_ranks_equal)

# S6: TOPSIS Chuẩn hóa Vector Cổ điển
def tinh_topsis_vector(X_raw, tieu_chi_dict, w_vec):
    norm = np.sqrt((X_raw ** 2).sum(axis=0))
    V = (X_raw / norm).multiply(w_vec, axis=1)
    
    A_plus = pd.Series(index=X_raw.columns, dtype=float)
    A_minus = pd.Series(index=X_raw.columns, dtype=float)
    
    for c in X_raw.columns:
        if tieu_chi_dict[c][2] > 0:
            A_plus[c] = V[c].max()
            A_minus[c] = V[c].min()
        else:
            A_plus[c] = V[c].min()
            A_minus[c] = V[c].max()
            
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    total_d = D_plus + D_minus
    CC = np.where(total_d == 0, 0.5, D_minus / total_d)
    res = pd.DataFrame({"TOPSIS_Score": CC}, index=X_raw.index)
    res["Rank"] = res["TOPSIS_Score"].rank(ascending=False, method="min").astype(int)
    return res

top_vec_ent = tinh_topsis_vector(X[list(TIEU_CHI.keys())], TIEU_CHI, w_entropy)
spear_vec_ent, _ = spearmanr(top_vec_ent["Rank"], s0_ranks_entropy)
tau_vec_ent, _ = kendalltau(top_vec_ent["Rank"], s0_ranks_entropy)
diff_vec_ent = (top_vec_ent["Rank"] - s0_ranks_entropy).abs()
overlap_vec_ent = len(set(top_vec_ent.sort_values("Rank").head(5).index).intersection(set(s0_ranks_entropy.sort_values().head(5).index)))

res_s6 = {
    "Scenario": "S6: Vector Normalization",
    "Criteria_Count": 6,
    "Spearman_Entropy": round(spear_vec_ent, 4),
    "Kendall_Entropy": round(tau_vec_ent, 4),
    "Mean_Rank_Diff_Entropy": round(diff_vec_ent.mean(), 2),
    "Max_Rank_Diff_Entropy": int(diff_vec_ent.max()),
    "Stations_Diff_ge5_Entropy": int((diff_vec_ent >= 5).sum()),
    "Top5_Overlap_Entropy": f"{overlap_vec_ent}/5",
    "Spearman_Equal": np.nan, "Kendall_Equal": np.nan, "Mean_Rank_Diff_Equal": np.nan, "Max_Rank_Diff_Equal": np.nan, "Stations_Diff_ge5_Equal": np.nan, "Top5_Overlap_Equal": "N/A",
}

all_res = [res_s0, res_s1, res_s2, res_s3, res_s4, res_s5, res_s6]
df_sensitivity = pd.DataFrame([{k: v for k, v in r.items() if not k.endswith("_df")} for r in all_res])

print("=== BẢNG TỔNG HỢP KIỂM ĐỊNH ĐỘ NHẠY THỨ HẠNG TOPSIS ===")
display(df_sensitivity)

# Biểu đồ so sánh độ nhạy thứ hạng
fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=200)
scen_labels = [r["Scenario"].split(":")[0] for r in all_res if r["Scenario"] != "S0: Gốc (C1-C6)"]
spear_vals = [r["Spearman_Entropy"] for r in all_res if r["Scenario"] != "S0: Gốc (C1-C6)"]
kend_vals = [r["Kendall_Entropy"] for r in all_res if r["Scenario"] != "S0: Gốc (C1-C6)"]

x = np.arange(len(scen_labels))
w = 0.35
ax.bar(x - w/2, spear_vals, width=w, label="Hệ số tương quan Spearman (\\rho)", color="#2b6cb0")
ax.bar(x + w/2, kend_vals, width=w, label="Hệ số tương quan Kendall (\\tau)", color="#4fd1c5")

for i, v in enumerate(spear_vals):
    ax.text(i - w/2, v + 0.015, f"{v:.3f}", ha="center", fontsize=7)
for i, v in enumerate(kend_vals):
    ax.text(i + w/2, v + 0.015, f"{v:.3f}", ha="center", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(scen_labels, fontsize=8)
ax.set_ylim(0.5, 1.08)
ax.set_ylabel("Hệ số tương quan thứ hạng so với S0", fontsize=8.5, fontweight="bold")
ax.set_title("Hình 3.10 — Độ nhạy thứ hạng TOPSIS (Entropy) qua các kịch bản kiểm định", fontsize=10.5, fontweight="bold", pad=12)
ax.legend(frameon=True, fontsize=8)
fig.tight_layout()
fig.savefig(THU_MUC_HINH / "hinh_3_10_phan_tich_do_nhay.png", bbox_inches="tight")
plt.show()
"""
))

# Section 11
cells.append(nbf.v4.new_markdown_cell(
"""## 9. Xuất dữ liệu báo cáo & Tổng kết hàm ý vận hành

Phần này xuất các bảng kết quả sang định dạng CSV phục vụ tích hợp báo cáo học thuật:
- `outputs/nv4_station_criteria.csv`: Ma trận 6 tiêu chí thô cấp trạm sạc.
- `outputs/nv4_criteria_weights.csv`: Trọng số Entropy và Trọng số đều đối chiếu.
- `outputs/nv4_topsis_rankings.csv`: Bảng điểm số và thứ hạng TOPSIS đầy đủ.
- `outputs/nv4_sensitivity_analysis.csv`: Bảng tổng hợp kiểm định độ nhạy qua các kịch bản.
"""
))

cells.append(nbf.v4.new_code_cell(
"""# Lưu các tệp CSV xuất bản
X.to_csv(THU_MUC_XUAT / "nv4_station_criteria.csv", encoding="utf-8-sig")

so_sanh_ts = bang_entropy[["Tên tiêu chí", "Entropy (e_j)", "Độ phân kỳ (d_j = 1 - e_j)", "Trọng số Entropy (w_j)"]].copy()
so_sanh_ts["Trọng số đều (w_j)"] = w_equal
so_sanh_ts["Chênh lệch (w_Entropy - w_Equal)"] = so_sanh_ts["Trọng số Entropy (w_j)"] - so_sanh_ts["Trọng số đều (w_j)"]
so_sanh_ts.to_csv(THU_MUC_XUAT / "nv4_criteria_weights.csv", encoding="utf-8-sig")

df_rank.to_csv(THU_MUC_XUAT / "nv4_topsis_rankings.csv", index=False, encoding="utf-8-sig")
df_sensitivity.to_csv(THU_MUC_XUAT / "nv4_sensitivity_analysis.csv", index=False, encoding="utf-8-sig")

print("-> [HOÀN TẤT] Toàn bộ dữ liệu và hình ảnh của NV4 đã được xuất thành công vào thư mục outputs/")
"""
))

nb['cells'] = cells

with open('notebooks/04_NV4_station_benchmarking.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Constructed notebook notebooks/04_NV4_station_benchmarking.ipynb successfully!")
