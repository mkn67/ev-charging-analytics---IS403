# Hướng dẫn chạy NV5 cho thành viên nhóm

NV5 dự báo **số cổng bị chiếm dụng** (`occupancy_ports`, mục tiêu chính) và **số phiên bắt đầu** (`session_arrivals`, mục tiêu phụ) theo từng cụm trạm, mỗi 15 phút. Toàn bộ mã chạy nằm trong `notebooks/05_NV5_demand_forecasting.ipynb`.

## 1. Chuẩn bị repo và môi trường

Dùng Python 3.10 trở lên. Mở terminal tại **thư mục gốc repo** (nơi có `requirements.txt` và `src/`).

**Windows PowerShell**

```powershell
git clone https://github.com/mkn67/ev-charging-analytics---IS403.git
cd ev-charging-analytics---IS403
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Linux/macOS**

```bash
git clone https://github.com/mkn67/ev-charging-analytics---IS403.git
cd ev-charging-analytics---IS403
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu đã clone repo, chỉ cần `git pull` rồi kích hoạt lại `.venv`. Khi mở notebook, chọn kernel Python thuộc `.venv`. Gói `xgboost-cpu` trong `requirements.txt` là bản CPU; notebook không cần GPU. [Hướng dẫn cài XGBoost chính thức](https://xgboost.readthedocs.io/en/stable/install.html).

## 2. Chuẩn bị dữ liệu đầu vào

`data/` bị Git ignore, nên người mới clone **không có dữ liệu NV1**. Tạo `data/raw/` và `data/processed/`, rồi chọn một trong hai cách sau:

1. **Nhanh nhất:** nhận hai file NV1 từ thành viên đã chạy NV1 và đặt đúng tên:
   - `data/processed/sessions_features.parquet`
   - `data/processed/sessions_clean.parquet`

   Notebook ưu tiên `sessions_features.parquet` và đối chiếu với `sessions_clean.parquet`. Nên nhận cả hai từ **cùng một lần xử lý NV1**.

2. **Tự dựng từ dữ liệu gốc:** đặt `EVChargingStationUsage.csv` vào `data/raw/`. Nếu không có `sessions_features.parquet`, NV5 sẽ tự gọi quy trình làm sạch NV1 từ CSV này. Cách này chậm hơn. Có thể chạy `notebooks/01_NV1_data_cleaning.ipynb` trước để tạo hai file parquet.

**Mapping trạm:** repo có `reports/station_cluster_map_example.csv` gồm 47 tên trạm và 9 cụm vị trí đang dùng. Nhóm kiểm tra lại mapping này theo thống nhất cuối cùng, rồi sao chép tới `data/processed/station_cluster_map.csv`.

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force data/raw, data/processed | Out-Null
Copy-Item reports/station_cluster_map_example.csv data/processed/station_cluster_map.csv
```

Linux/macOS:

```bash
mkdir -p data/raw data/processed
cp reports/station_cluster_map_example.csv data/processed/station_cluster_map.csv
```

**Mốc thời gian:** `reports/nv5_splits.json` đã có trong repo: train kết thúc 01/01/2019, validation kết thúc 01/07/2019, test kết thúc 01/01/2020; stress test từ 01/01/2020 đến trước 01/01/2021. Các mốc đều là UTC và là ranh giới **không bao gồm điểm kết thúc**. Chỉ sửa sau khi nhóm thống nhất, vì đổi mốc sẽ làm metric không còn so sánh trực tiếp được.

Trước khi chạy, kiểm tra tối thiểu có:

```text
data/processed/station_cluster_map.csv
reports/nv5_splits.json
data/processed/sessions_features.parquet + sessions_clean.parquet
    HOẶC data/raw/EVChargingStationUsage.csv
```

## 3. Chạy notebook

Từ thư mục gốc repo:

```bash
python -m jupyter lab
```

Mở `notebooks/05_NV5_demand_forecasting.ipynb`, chọn kernel `.venv`, rồi chạy **Restart Kernel and Run All Cells**. Cell audit trước cell cuối kiểm tra dữ liệu và ghi `outputs/nv5/nv5_input_audit.json`. Cell cuối dựng chuỗi, fit từng cụm và xuất kết quả. Tránh chạy lại riêng cell cuối nhiều lần vì nó huấn luyện lại toàn bộ mô hình.

Notebook xử lý 9 cụm theo thứ tự, dùng Random Forest và XGBoost trên CPU. Cần đủ RAM và chỗ trống đĩa; riêng hai CSV dự báo/chuỗi của lần chạy hiện tại chiếm khoảng **0,8 GB**. Thời gian chạy tùy máy.

## 4. Kiểm tra kết quả

Các file chính trong `outputs/nv5/`:

| File | Nội dung |
|---|---|
| `nv5_input_audit.json` | Kiểm tra dữ liệu NV1, mapping và mốc chia |
| `data_audit.json` | Số phiên giữ/loại, 9 cụm, giới hạn occupancy quan sát |
| `timeseries_15min.csv` | Chuỗi mục tiêu 15 phút theo cụm |
| `nv5_model_comparison.csv` | MAE, RMSE, R² theo cụm, mục tiêu, mô hình, giai đoạn |
| `baseline_predictions.csv` | Giá trị thực và dự báo theo từng timestamp |

Với mapping và split hiện tại, bảng `nv5_model_comparison.csv` có **378 dòng**: 9 cụm × 2 mục tiêu × 7 mô hình × 3 giai đoạn (`validation`, `test`, `stress_2020`). Bảy mô hình gồm Historical Mean, persistence `t-1`/`t-96`/`t-672`, Ridge, Random Forest và XGBoost. Khi báo cáo kết quả cuối, dùng **test 2019**; trình bày **stress 2020** riêng. `session_arrivals` là mục tiêu phụ, không thay cho occupancy.

`outputs/` bị Git ignore. Các file kết quả nằm trên máy người chạy, **không tự xuất hiện trên GitHub**; nếu nhóm cần ghép báo cáo, hãy chia sẻ bảng metric hoặc số liệu cần dùng qua kênh lưu trữ của nhóm. Các PNG/CSV metric cũ nếu có trong bản sao cục bộ có thể thuộc lần chạy trước; dùng timestamp và `nv5_model_comparison.csv` của lần chạy mới nhất.

## 5. Lỗi thường gặp

- **Thiếu `station_cluster_map.csv`:** sao chép file trong `reports/` như bước 2; bảo đảm cả hai cột `station_name,cluster_id` đều có giá trị.
- **Thiếu dữ liệu NV1:** nhận hai parquet cùng lần chạy hoặc đặt CSV gốc đúng tên vào `data/raw/`.
- **Thiếu `nv5_splits.json`:** cập nhật repo; file này đã được theo dõi bởi Git.
- **`ModuleNotFoundError` hoặc kernel sai:** kích hoạt `.venv`, cài lại `requirements.txt`, chọn kernel của `.venv`.
- **Dữ liệu clean/features không khớp:** xin lại hai parquet cùng nguồn hoặc dùng CSV gốc để chạy lại NV1; không ghép parquet từ hai lần làm sạch khác nhau.
- **Máy hết RAM/dung lượng:** đóng ứng dụng nặng, bảo đảm còn chỗ cho CSV đầu ra; nếu cần, chạy trên máy nhóm có RAM lớn hơn. Không đổi mốc chia hoặc bỏ cụm để xử lý lỗi bộ nhớ vì như vậy kết quả sẽ không tương đương.

Giải thích phương pháp và các giới hạn kết luận ở `reports/NV5_demand_forecasting.md` và `reports/3.5_3.6_phuong_phap_du_bao_va_danh_gia.md`.
