# NV5 — Dự báo nhu cầu sạc và mức độ chiếm dụng trạm sạc (bản thực nghiệm)

## 1. Mục tiêu và cơ sở nghiên cứu

Đồ án IS403 đặt ra bài toán dự báo ở độ phân giải **15 phút**, sử dụng các mô hình đối chứng (Historical Mean, Persistence theo ngày/tuần, Ridge) và mô hình đề xuất XGBoost. Theo Ostermann et al. (2022), nghiên cứu về dự báo tình trạng chiếm dụng cổng sạc cần làm rõ đầu ra (từng cổng hay mức chiếm dụng tổng hợp) và đánh giá so với baseline. Bản thực nghiệm này dự báo đồng thời:

- **`occupancy_ports` (cổng):** số phiên kết nối đang giao với một khoảng 15 phút trên toàn tập dữ liệu; được suy từ thời điểm bắt đầu và kết thúc phiên sạc. Đây là **proxy của số cổng đang được sử dụng**, không phải số liệu trạng thái thiết bị đo trực tiếp. Các bản ghi cùng cổng nếu chồng lấn có thể bị đếm hai lần.
- **`session_arrivals` (phiên/15 phút):** số phiên bắt đầu trong từng khoảng 15 phút; phản ánh lượng phiên đến, không trực tiếp bằng nhu cầu chưa được phục vụ.

Thêm `session_energy_kwh_at_start` phục vụ tham khảo: là **tổng điện năng cả phiên được gán về thời điểm bắt đầu**, hoàn toàn **không phải tải điện đo theo 15 phút**. Không sử dụng biến này để khẳng định công suất phụ tải hay quá tải lưới.

## 2. Chuẩn hóa và tạo chuỗi

Dùng bản `sessions_features.parquet` và `is_valid_session` theo NV1 khi môi trường có `pyarrow`. Nếu không đọc được parquet, script chạy lại hàm `build_clean_pipeline` hiện hữu của NV1 từ CSV gốc, giữ logic đánh cờ phiên hợp lệ của repo. Mốc thời gian dùng UTC đúng với dữ liệu NV1. Xây lưới 15 phút đều đặn; các khoảng không có phiên được điền 0. Mỗi phiên được tính là chiếm dụng các khung 15 phút giao với `[start_datetime_utc, end_datetime_utc)`. Không suy diễn điện năng/công suất từng khung từ thời lượng kết nối.

## 3. Phương pháp học máy và kiểm soát leakage

Dùng đặc trưng lịch `slot` (0–95), thứ, tháng, weekend, sin/cos chu kỳ; đặc trưng trễ tại 1, 4, 96 và 672 khoảng; trung bình trượt 4/96/672 khoảng **đều shift(1) trước khi tính**. Mỗi mục tiêu tạo một bảng feature riêng, không dùng occupancy của cùng thời điểm để dự báo arrivals hoặc ngược lại.

Chia **80% đầu thời gian** để train, **20% cuối** để test, không shuffle. Historical Mean tính từ **train**, theo `(thứ trong tuần, slot 15 phút)`; Persistence Day và Week dùng giá trị thực trước đó; Ridge, Random Forest và XGBoost huấn luyện chỉ bằng train. Random Forest dùng tối đa 100.000 dòng train lấy đều theo thứ tự để giảm RAM và thời gian chạy trên laptop; cần nêu rõ hạn chế này khi so sánh.

Đây là đánh giá **one-step-ahead với dữ liệu lịch sử được cập nhật liên tục**, không phải dự báo nhiều bước hoàn toàn tự hồi quy trong tương lai. Vì lag-1 sử dụng giá trị quan sát trước đó (tại `t-1`), không được diễn giải thành dự báo một tuần trước mà không có quan sát cập nhật.

## 4. Kết quả thực nghiệm

Môi trường chạy kiểm tra không có `pyarrow` và không thể cài trực tuyến; kết quả dưới đây được chạy từ CSV gốc bằng **chính pipeline làm sạch NV1 trong repository**, không phải đọc trực tiếp Parquet. Số liệu này cần được chạy kiểm chứng trong môi trường Python của nhóm.

### 4.1. Chiếm dụng cổng sạc

| Mô hình | MAE (cổng) | RMSE (cổng) | R² |
|---|---:|---:|---:|
| Historical Mean | 5.9228 | 7.9554 | 0.3990 |
| Lag-1 Day | 3.2939 | 5.1332 | 0.7498 |
| Lag-1 Week | 2.9398 | 4.6066 | 0.7985 |
| Ridge | 0.8992 | 1.3792 | 0.9819 |
| Random Forest | 0.8662 | 1.3712 | 0.9821 |
| **XGBoost** | **0.8556** | **1.3540** | **0.9826** |

### 4.2. Nhu cầu phiên bắt đầu

| Mô hình | MAE (phiên/15 phút) | RMSE (phiên/15 phút) | R² |
|---|---:|---:|---:|
| Historical Mean | 0.7915 | 1.2539 | 0.2348 |
| Lag-1 Day | 0.7876 | 1.3807 | 0.0722 |
| Lag-1 Week | 0.7723 | 1.3594 | 0.1007 |
| Ridge | 0.6749 | 1.0264 | 0.4873 |
| Random Forest | 0.6580 | 1.0233 | 0.4904 |
| **XGBoost** | **0.6441** | **1.0131** | **0.5005** |

Dữ liệu dùng để đánh giá: **259.344 phiên hợp lệ**, 139 cổng quan sát được, 330.920 khung 15 phút; loại 672 khung đầu để tạo lag. Train 264.198 khung, test 66.050 khung; test bắt đầu **2019-02-17 04:45 UTC**. Kết quả model cho nhu cầu đến có R² khoảng 0.50, kém rõ rệt so với dự báo occupancy: không nên tuyên bố hai bài toán có độ chính xác tương đương.

## 5. Diễn giải và giới hạn

1. XGBoost tốt nhất trên tập test theo RMSE, nhưng chênh lệch so với Random Forest nhỏ. Chưa có kiểm định độ ổn định theo nhiều cửa sổ thời gian; chưa chứng minh mô hình tốt hơn ở mọi trạm hay mọi giai đoạn.
2. Chưa có thông tin đầy đủ về **công suất vật lý, số cổng hoạt động theo từng thời kỳ**, hoặc tình trạng hỏng thiết bị. Do đó không dùng 139 cổng quan sát toàn kỳ làm mẫu số chính xác cho tỷ lệ chiếm dụng tại mọi thời điểm; không được công bố giờ “quá tải” như kết luận thực tế.
3. Những kỳ gần năm 2020 có thể ảnh hưởng bởi biến động nhu cầu, làm giảm tính ổn định của phân phối. Cần thêm rolling backtest và phân tích theo giai đoạn để khẳng định độ bền vững.
4. Thời gian UTC chưa phản ánh giờ sinh hoạt địa phương một cách trực quan, đặc biệt do thay đổi PDT/PST; nên bổ sung biểu đồ giờ địa phương với timezone `America/Los_Angeles` nếu phần kết quả đưa vào khuyến nghị vận hành.
5. Các biến mục tiêu là dạng đếm nguyên không âm nhưng mô hình hồi quy có thể cho giá trị thực; đã chặn dự báo âm về 0, không làm tròn trước khi tính metrics.
6. Các đặc trưng và so sánh là thiết kế nghiên cứu của đồ án; không sao chép số liệu thành công của Ostermann (2022) sang kết quả thực nghiệm của nhóm.

## 6. Hướng tái lập và vị trí kết quả

Chạy từ gốc repo:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements_nv5.txt
python scripts/nv5_forecasting.py
python -m pytest tests/test_nv5_forecasting.py -q
```

Bảng kết quả và biểu đồ xuất ra `outputs/nv5/`. Notebook `notebooks/05_NV5_demand_forecasting.ipynb` trình bày tuần tự code và các kết quả. Ghi chú: file `timeseries_15min.csv` (~10 MB) là dữ liệu phát sinh, có thể tự tái tạo và không cần commit nếu nhóm muốn giữ PR gọn.

### Nguồn nghiên cứu

- Ostermann, A., Fabel, Y., Ouan, K. & Koo, H. (2022). *Forecasting Charging Point Occupancy Using Supervised Learning Algorithms*. Energies 15(9), 3409. DOI: 10.3390/en15093409.
- Luo, S. & Wang, Y. (2025). *The impacts of rate surge on electric vehicle charging behaviors: Evidence from California*. Journal of Economic Behavior & Organization 236, 107048. DOI: 10.1016/j.jebo.2025.107048.
- Bayram, I. S. et al. (2023). *Statistical Characterization of Public AC EV Chargers in the U.K.* IEEE Access. DOI: 10.1109/ACCESS.2023.3293091.
