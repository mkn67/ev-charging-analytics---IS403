# Hướng dẫn chạy toàn bộ NV1–NV5

Tài liệu này dành cho thành viên mới clone repo và muốn tạo lại kết quả từ dữ liệu gốc. Chạy lệnh tại **thư mục gốc dự án** (nơi có `requirements.txt`, `src/`, `notebooks/`). Khi mở notebook trong Jupyter, giữ nguyên vị trí của notebook trong thư mục `notebooks/` vì NV2 và NV3 dùng đường dẫn tương đối.

## 1. Chuẩn bị một lần

Yêu cầu: Python 3.10 trở lên, đủ dung lượng đĩa cho dữ liệu và kết quả NV5 (riêng hai CSV lớn khoảng 0,8 GB), và file gốc `EVChargingStationUsage.csv`. File gốc và thư mục `outputs/` không nằm trên GitHub vì được Git ignore.

### Windows PowerShell

```powershell
git clone https://github.com/mkn67/ev-charging-analytics---IS403.git
cd ev-charging-analytics---IS403
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data/raw, data/processed | Out-Null
```

### Linux/macOS

```bash
git clone https://github.com/mkn67/ev-charging-analytics---IS403.git
cd ev-charging-analytics---IS403
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
mkdir -p data/raw data/processed
```

Nếu đã clone, cập nhật bằng `git pull`, kích hoạt lại `.venv`, rồi cài lại `requirements.txt` khi danh sách thư viện thay đổi. Đặt dữ liệu gốc tại:

```text
data/raw/EVChargingStationUsage.csv
```

Tên file phải đúng như trên. Không cần sửa mã để trỏ tới file trong thư mục Downloads của một thành viên khác. Mở Jupyter từ thư mục gốc bằng `python -m jupyter lab`, rồi chọn kernel Python của `.venv` cho từng notebook. Trong Jupyter, dùng **Restart Kernel and Run All Cells** để tránh kết quả từ biến cũ.

## 2. Thứ tự chạy

| Bước | Chạy gì | Đầu vào cần có | Kết quả cần kiểm tra |
|---|---|---|---|
| NV1 | `notebooks/01_NV1_data_cleaning.ipynb`, sau đó `python -m src.run_pipeline` | CSV gốc | `data/processed/sessions_clean.parquet`, `sessions_features.parquet`; `outputs/tables/data_quality_audit_summary.csv` |
| NV2 | `notebooks/02_NV2_occupancy_clustering.ipynb` | CSV gốc | Bảng/chỉ số trong notebook và `outputs/nv2/` (chỉ số, hồ sơ cụm, metadata) |
| NV3 | `notebooks/03_NV3_policy_evaluation.ipynb` | `sessions_features.parquet` từ NV1 | `notebooks/outputs_nv3_v6/` với audit, bảng phân đoạn, thống kê và bunching |
| NV4 | `notebooks/04_NV4_station_benchmarking.ipynb` | CSV gốc; parquet NV1 để đối soát nếu có | `outputs/nv4_*.csv`, `outputs/nv4_run_metadata.json`, `outputs/nv4_rank_robustness.json` |
| NV5 | `notebooks/05_NV5_demand_forecasting.ipynb` | Parquet NV1, mapping trạm, file mốc chia | `outputs/nv5/nv5_model_comparison.csv`, chuỗi và dự báo |

### NV1 — làm sạch và tạo đặc trưng

Chạy hết notebook NV1 để xem các kiểm tra dữ liệu. **Sau đó, từ terminal ở thư mục gốc, chạy thêm:**

```bash
python -m src.run_pipeline
```

Lệnh này tạo **cả hai** file `sessions_clean.parquet` và `sessions_features.parquet` từ cùng một lần xử lý, cùng bảng audit và hình. Chỉ chạy notebook NV1 thì chưa có `sessions_features.parquet` cho NV3. Kiểm tra hai file trong `data/processed/` trước khi sang NV3/NV5. Bảng audit còn ghi các cờ múi giờ không nhận diện, khoảng kết nối không dương và độ lệch thời lượng so với timestamp quá 59 giây. Các cờ này phục vụ đối soát; `is_valid_session` vẫn theo định nghĩa cũ, nên cần ghi rõ bộ lọc riêng của mỗi NV.

### NV2 — phân cụm hành vi phiên

Notebook NV2 tự đọc `data/raw/EVChargingStationUsage.csv` theo thư mục gốc dự án. Nó tự làm sạch cho thí nghiệm phân cụm, gồm ngưỡng công suất 19,2 kW và kiểm tra timestamp 59 giây; lượt chạy hiện hành còn 258.720 phiên, khác 259.356 phiên theo `is_valid_session` của NV1. Các bảng lựa chọn k, DBSCAN, hồ sơ cụm và metadata của **cùng lượt chạy** được xuất vào `outputs/nv2/`. Không ghép chúng với `outputs/tables/kmeans_*.csv` từ mẫu khác. **Cluster hành vi NV2 không phải 9 cụm vị trí của NV4/NV5.**

### NV3 — đánh giá chính sách

Notebook NV3 đọc `../data/processed/sessions_features.parquet` từ thư mục `notebooks/`. Nếu báo thiếu file, quay lại chạy `python -m src.run_pipeline`. Các file CSV và hình được lưu dưới `notebooks/outputs_nv3_v6/`. Bảng phân đoạn có nhóm `New_Post` cho người dùng chỉ xuất hiện giai đoạn sau. Khi diễn giải thay đổi, ưu tiên Delta và khoảng tin cậy bootstrap theo User ID ở `3.3.3_stats.csv`; nhãn `Chưa rõ` nghĩa là khoảng tin cậy chứa 0, dù p-value Mann–Whitney có thể nhỏ.

### NV4 — đánh giá trạm

Notebook NV4 đọc CSV gốc, so sánh với parquet NV1 nếu có, rồi lưu bảng ở `outputs/`. Chạy hết các cell theo thứ tự; file quan trọng để xem thứ hạng là `outputs/nv4_topsis_rankings.csv`, còn `outputs/nv4_run_metadata.json` ghi thông tin lượt chạy. `outputs/nv4_rank_robustness.json` cho biết tương quan giữa tiêu chí và mức đổi hạng ở S1/S2/S6; đọc file này trước khi coi thứ hạng là ổn định. Script `scripts/generate_all_nv4_assets.py` là cách tạo lại bảng/hình NV4 từ terminal, không cần chạy thêm nếu đã chạy notebook và chỉ cần bảng kết quả.

### NV5 — dự báo 15 phút

Trước khi chạy cell cuối, cần có hai cấu hình:

1. `data/processed/station_cluster_map.csv` gồm `station_name,cluster_id`. Nếu nhóm dùng mapping mẫu đã thống nhất, sao chép `reports/station_cluster_map_example.csv` tới đường dẫn này. Kiểm tra lại mapping trước khi dùng; không điền `cluster_id` tùy ý.
2. `reports/nv5_splits.json` đã có trong repo: train đến trước 01/01/2019, validation đến trước 01/07/2019, test đến trước 01/01/2020, stress riêng trong năm 2020. Các mốc là UTC.

Sao chép mapping bằng một trong hai lệnh sau:

```powershell
# Windows PowerShell
Copy-Item reports/station_cluster_map_example.csv data/processed/station_cluster_map.csv
```

```bash
# Linux/macOS
cp reports/station_cluster_map_example.csv data/processed/station_cluster_map.csv
```

Chạy hết notebook NV5. Cell audit lưu `outputs/nv5/nv5_input_audit.json`; cần thấy mapping và mốc chia hợp lệ. Cell cuối huấn luyện riêng theo cụm và lưu `outputs/nv5/nv5_model_comparison.csv`. Với cấu hình hiện tại, bảng này có **378 dòng**: 9 cụm × 2 mục tiêu × 7 mô hình × 3 giai đoạn. Mục tiêu chính là số cổng bị chiếm (`occupancy_ports`); `session_arrivals` là mục tiêu phụ. Chạy NV5 có thể tốn thời gian và tạo hai CSV lớn; tránh bấm chạy cell cuối nhiều lần. Xem chi tiết tại `docs/HUONG_DAN_CHAY_NV5.md`.

## 3. Khi chạy xong, gửi gì cho nhóm?

- NV1: số phiên hợp lệ, bảng audit và hai file parquet nếu người khác cần chạy NV3/NV5 mà không có CSV gốc.
- NV2: các bảng trong `outputs/nv2/`, gồm chỉ số, hồ sơ cụm và metadata cùng lượt chạy.
- NV3: các CSV trong `notebooks/outputs_nv3_v6/` và hình bunching.
- NV4: `outputs/nv4_topsis_rankings.csv`, bảng tiêu chí/trọng số, `outputs/nv4_rank_robustness.json` và metadata của cùng lượt chạy.
- NV5: `outputs/nv5/nv5_model_comparison.csv`, kèm mapping và `reports/nv5_splits.json` đã dùng. Báo cáo test 2019 và stress 2020 riêng; so cả MAE, RMSE, R².

`outputs/` và `notebooks/outputs_*/` bị Git ignore. Kết quả tạo trên máy **không tự xuất hiện trên GitHub**; chia sẻ qua kênh lưu trữ của nhóm nếu cần. Không đưa CSV dữ liệu gốc hoặc `baseline_predictions.csv` rất lớn vào commit.

## 4. Lỗi hay gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `FileNotFoundError` ở NV1/NV2/NV4 | Kiểm tra `data/raw/EVChargingStationUsage.csv` và tên file; mở Jupyter từ thư mục gốc repo. |
| NV3 thiếu `sessions_features.parquet` | Chạy `python -m src.run_pipeline` sau NV1. |
| NV5 thiếu mapping | Sao chép file mapping mẫu vào `data/processed/` và kiểm tra đủ hai cột. |
| `ModuleNotFoundError: statsmodels` hoặc `xgboost` | Kích hoạt `.venv`, chạy `python -m pip install -r requirements.txt`, chọn đúng kernel. |
| Kết quả không đổi sau khi sửa cell | Restart Kernel and Run All Cells. |
| Máy thiếu RAM/dung lượng khi chạy NV5 | Đóng các ứng dụng nặng và dành ít nhất khoảng 1 GB dung lượng trống cho CSV đầu ra; chạy trên máy có nhiều RAM hơn nếu cần. |
| `git push` từ chối file lớn | Không commit dữ liệu hay output; `.gitignore` của repo đã loại `data/`, `outputs/` và `notebooks/outputs_*/`. |
