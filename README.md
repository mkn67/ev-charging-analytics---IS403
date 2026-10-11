# EV Charging Analytics (ev-charging-analytics)

> **Đồ án Chuyên ngành Business Analyst:** Phân tích hành vi sạc, đánh giá hiệu suất khai thác và tối ưu hóa chính sách vận hành trạm sạc xe điện (Electric Vehicle Charging Stations).

---

## 1. Cấu trúc thư mục dự án (Project Tree)

```text
ev-charging-analytics/
├── data/
│   ├── raw/                         # Dataset gốc, không chỉnh sửa
│   ├── interim/                     # Dữ liệu trung gian
│   └── processed/
│       ├── sessions_clean.parquet   # Dữ liệu sạch sau NV1
│       └── sessions_features.parquet# Dữ liệu trích xuất đặc trưng (T_idle, Idle Ratio, thời gian)
│
├── notebooks/
│   ├── 01_NV1_data_cleaning.ipynb            # Tiền xử lý & kiểm soát chất lượng dữ liệu (NV1)
│   ├── 02_NV2_occupancy_clustering.ipynb      # Phân cụm hành vi chiếm dụng trạm sạc (NV2)
│   ├── 03_NV3_policy_evaluation.ipynb         # Đánh giá & mô phỏng chính sách phí nhàn rỗi (NV3)
│   ├── 04_NV4_station_benchmarking.ipynb      # Đánh giá hiệu suất và xếp hạng trạm sạc (NV4)
│   └── 05_NV5_demand_forecasting.ipynb        # Dự báo nhu cầu sạc và phụ tải trạm (NV5)
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # Đường dẫn, hằng số vật lý và tham số dùng chung
│   ├── data_validation.py           # Bộ hàm kiểm tra tính toàn vẹn logic và giới hạn vật lý
│   ├── feature_engineering.py       # Tính toán T_idle, Idle Ratio và các đặc trưng thời gian
│   ├── evaluation.py                # Metric đánh giá chất lượng dữ liệu, trạm sạc và mô hình
│   ├── visualization.py             # Hàm vẽ biểu đồ phân phối, boxplot, công suất sạc
│   └── run_pipeline.py              # Script thực thi tự động pipeline tiền xử lý NV1
│
├── outputs/
│   ├── tables/                      # Bảng kết quả CSV (Audit scorecard, KPIs)
│   ├── figures/                     # Biểu đồ phân tích định dạng PNG/PDF
│   ├── models/                      # Mô hình học máy đã huấn luyện
│   └── metrics/                     # Kết quả đánh giá chỉ số mô hình
│
├── reports/
│   ├── figures/                     # Biểu đồ độ phân giải cao phục vụ chèn vào báo cáo Word/PDF
│   └── 2.2_kiem_soat_chat_luong_va_tien_xu_ly_du_lieu.md  # Nội dung học thuật mục 2.2
│
├── tests/
│   └── test_data_integrity.py       # Bộ kiểm thử tự động pytest kiểm tra tính toàn vẹn
│
├── .gitignore                       # Danh sách loại trừ commit Git
├── README.md                        # Tài liệu hướng dẫn dự án
└── requirements.txt                 # Danh mục thư viện Python
```

---

## 2. Các nhiệm vụ phân tích trọng tâm (NV1 - NV5)

| Mã NV | Nhiệm vụ | Notebook | Mô tả chi tiết |
| :--- | :--- | :--- | :--- |
| **NV1** | **Kiểm soát chất lượng & Tiền xử lý dữ liệu** *(Dung làm)* | `01_NV1_data_cleaning.ipynb` | Thiết lập 6 quy tắc toàn vẹn logic, xử lý lỗi đa múi giờ (PST/PDT/UTC), số serial Excel, nhận diện dị biệt công suất vật lý ($P_{avg} = 419,4\text{ kW}$ tại TED THOMPSON #1), phân tích ngoại lệ thống kê IQR và phân lập Zero-Energy Sessions. |
| **NV2** | **Phân cụm hành vi chiếm dụng trạm** | `02_NV2_occupancy_clustering.ipynb` | Ứng dụng K-Means / GMM phân loại hồ sơ hành vi người dùng dựa trên thời gian nhàn rỗi ($T_{idle}$) và $Idle\ Ratio$. |
| **NV3** | **Đánh giá & mô phỏng chính sách phí** | `03_NV3_policy_evaluation.ipynb` | Mô phỏng chính sách phí nhàn rỗi (Overstay fee) với thời gian miễn trừ (Grace period) 15m/30m nhằm giảm thiểu tắc nghẽn và ước tính doanh thu. |
| **NV4** | **Đánh giá hiệu suất & Xếp hạng trạm sạc** | `04_NV4_station_benchmarking.ipynb` | Đo lường hệ số sử dụng (Utilization Rate), phân tích ma trận 4 góc phần tư xác định trạm quá tải cần mở rộng cổng. |
| **NV5** | **Dự báo nhu cầu sạc & phụ tải** | `05_NV5_demand_forecasting.ipynb` | Tổng hợp chuỗi thời gian phụ tải theo giờ, huấn luyện mô hình Machine Learning dự báo nhu cầu năng lượng (MAE, RMSE, MAPE). |

---

## 3. Hướng dẫn cài đặt và thực thi

### Bước 1: Khởi tạo và kích hoạt môi trường ảo
```powershell
# Kích hoạt môi trường ảo .venv đã tạo
.\.venv\Scripts\Activate.ps1
```

### Bước 2: Cài đặt các thư viện cần thiết
```powershell
pip install -r requirements.txt
```

### Bước 3: Thực thi tự động pipeline tiền xử lý (NV1)
```powershell
# Chạy pipeline tạo sessions_clean.parquet, sessions_features.parquet và các bảng biểu đồ
python -m src.run_pipeline
```

### Bước 4: Chạy bộ kiểm thử tự động kiểm tra chất lượng dữ liệu
```powershell
pytest tests/test_data_integrity.py -v
```

---

## 4. Bảng tổng kết chất lượng dữ liệu (NV1 Audit Scorecard)

Dữ liệu gốc ghi nhận **259.415 dòng**. Sau khi kiểm tra theo 6 quy tắc toàn vẹn và giới hạn vật lý:
- **Bản ghi trùng lặp hoàn toàn:** 4 dòng (đã loại bỏ).
- **Vi phạm logic thời lượng ($T_{charging} > T_{total}$):** 45 dòng (gắn cờ `flag_charging_gt_total`, không gán idle time âm về 0).
- **Dị biệt công suất vật lý ($P_{avg} > 22\text{ kW}$):** 10 dòng (gắn cờ `flag_physical_power_anomaly`).
- **Giao dịch không phát sinh điện năng ($E = 0$):** 0 dòng (toàn bộ $E > 0$).
- **Xung đột thời gian trên cùng cổng sạc:** 181 phiên trên 29 cổng (`flag_port_overlap`).
- **Số phiên hợp lệ đầy đủ đưa vào phân tích:** **259.356 phiên** (chiếm **99,979%**).

