# NV5 — Dự báo occupancy cổng và session arrivals (mục 3.5.1–3.5.2)

## 3.5.1. Định nghĩa mục tiêu và tạo chuỗi 15 phút

NV5 gán cluster_id theo vị trí ghi trong Station Name, không theo cluster hành vi phiên của NV2. 47 cách viết tên trạm được gom về 9 họ vị trí nêu trong đề cương: BRYANT, CAMBRIDGE, HAMILTON, HIGH, MPL, RINCONADA LIB, SHERMAN, TED THOMPSON và WEBSTER. Crosswalk đã được điền tại data/processed/station_cluster_map.csv; file mẫu nằm ở reports/station_cluster_map_template.csv. Gán theo từng phiên xử lý đúng hai cổng chuẩn hóa cùng MAC/cổng xuất hiện ở HAMILTON #2 đến tháng 01/2016 và BRYANT #3 từ tháng 01/2016 trở đi. Mapping tĩnh theo port_id sẽ gán sai một giai đoạn.

`port_id` của NV1 được tạo từ `MAC Address` và `Port Number` theo dạng `{MAC Address}_Port_{Port Number}`. Dữ liệu có 139 cách ghi `port_id` gốc. Sau khi chuẩn hóa dấu phân tách và chữ hoa/thường của MAC, chúng quy về 117 ID MAC/cổng chuẩn; mapping mẫu dùng danh sách chuẩn này để không tạo hai mapping cho cùng một cổng vật lý. NV5 kiểm tra lại quan hệ này khi nạp dữ liệu. Nếu thiếu một thành phần định danh, NV1 để `port_id` rỗng thay vì tạo chuỗi giả như `nan_Port_nan`.

NV5 ưu tiên `sessions_features.parquet`, đồng thời đối chiếu số dòng, số phiên hợp lệ và khóa phiên với `sessions_clean.parquet`. Nếu parquet không đọc được hoặc hai bảng không khớp, NV5 chạy lại `build_clean_pipeline` của NV1 từ CSV gốc. Trên dữ liệu hiện tại:

- Hai parquet đều có 259.411 dòng, 259.356 phiên `is_valid_session=True` và cùng khóa phiên.
- CSV có 259.415 dòng; NV1 loại 4 dòng trùng nguyên văn, còn 259.411 dòng.
- Có 12 phiên hợp lệ theo cờ NV1 nhưng có `end_datetime_utc == start_datetime_utc`. NV5 loại 12 phiên thời lượng bằng 0 khỏi chuỗi khoảng; không có khoảng kết thúc trước lúc bắt đầu. Do đó 259.344 trong kết quả NV5 cũ là số sau bộ lọc khoảng thời gian dương, không phải chênh lệch giữa hai parquet hay do nhánh fallback.

Mỗi chuỗi có lưới UTC đều đặn 15 phút trên cùng khoảng thời gian. Khoảng hoạt động dùng quy ước nửa mở `[start_datetime_utc, end_datetime_utc)`: phiên kết thúc đúng ranh giới không chiếm khung tiếp theo. Các khung không có hoạt động được điền 0.

- **`occupancy_ports` (cổng):** số `port_id` vật lý riêng biệt có ít nhất một phiên giao với khung 15 phút, tính riêng từng cluster. Hai phiên chồng lấn cùng cổng chỉ tính một; hai cổng khác nhau tính hai. Bản ghi thiếu `port_id` không làm tăng occupancy.
- **`session_arrivals` (phiên/khung):** số phiên bắt đầu trong khung, tính riêng từng cluster. Đây là lượng phiên bắt đầu, không phải số cổng đang bận.
- **Phụ tải điện:** không phải mục tiêu trong NV5. Tổng kWh của cả phiên không được phân bổ thành kWh hay kW theo khung 15 phút; vì thế không dùng occupancy hoặc arrivals để kết luận công suất hay quá tải lưới.

Các phiên hợp lệ nhưng thiếu `port_id` vẫn có thể đóng góp arrivals nếu nhóm cung cấp được `cluster_id` đáng tin cậy cho chúng; nếu thiếu cả cluster, phiên không thể phân bổ theo cụm và được ghi trong audit. Occupancy luôn bỏ qua các phiên thiếu `port_id`.

## 3.5.2. Baseline và giao thức đánh giá

Mọi baseline được fit/tính riêng theo cluster_id. Giao diện nhận mốc train, validation, test trong JSON; chương trình không tự chia 80/20. Các mốc là ranh giới kết thúc loại trừ train_end_utc, validation_end_utc, test_end_utc. File hiện dùng mốc đề xuất trong proposal.

- **Historical Mean:** trung bình mục tiêu của train theo thứ trong tuần và slot 15 phút, riêng từng cluster. Nếu một slot chưa xuất hiện trong train, dùng trung bình train của cluster đó.
- **Persistence Step (`t-1`), Day (`t-96`) và Week (`t-672`):** lấy giá trị lịch sử cùng cluster, không trộn giữa các cluster.
- **Ridge:** scaler được fit chỉ trên train của cluster; cùng scaler transform validation/test. Không fit lại scaler trên validation/test.
- **Random Forest:** đối chứng cây với 60 cây, độ sâu tối đa 12, tối thiểu 4 mẫu ở mỗi lá; fit từng cluster với 2 luồng.
- **XGBoost Regressor:** chọn giữa hai cấu hình định trước theo RMSE validation, sau đó đánh giá trên test; fit riêng trên train của từng cluster.

Đánh giá là one-step-ahead: các lag trong validation/test dùng quan sát quá khứ đã có tại thời điểm dự báo. Dữ liệu được chia theo thời gian, không xáo trộn: train kết thúc 2019-01-01, validation kết thúc 2019-07-01, test kết thúc 2020-01-01; giai đoạn stress riêng từ 2020-01-01 đến trước 2021-01-01. Mốc test/stress không tham gia chọn cấu hình.

### Đầu vào bắt buộc từ nhóm

1. Crosswalk `data/processed/station_cluster_map.csv` có hai cột station_name,cluster_id và 47 tên trạm ánh xạ vào 9 họ vị trí. `port_id` được chuẩn hóa riêng để đếm cổng vật lý trong occupancy.
2. Mốc thời gian đã được ghi trong `reports/nv5_splits.json`:

```json
{
  "train_end_utc": "2019-01-01T00:00:00Z",
  "validation_end_utc": "2019-07-01T00:00:00Z",
  "test_end_utc": "2020-01-01T00:00:00Z",
  "stress_start_utc": "2020-01-01T00:00:00Z",
  "stress_end_utc": "2021-01-01T00:00:00Z"
}
```

Stress test chỉ gồm năm 2020 và không tham gia chọn mô hình.

Toàn bộ mã NV5 được đặt trong `notebooks/05_NV5_demand_forecasting.ipynb`; thư mục `scripts/` chỉ chứa script chương 4. Mở notebook, chạy lần lượt các cell định nghĩa rồi chạy cell cuối sau khi điền hai đầu vào. Có thể chạy notebook bằng Jupyter từ thư mục gốc repo.

### Bảng bàn giao và kiểm tra

Notebook xuất `outputs/nv5/timeseries_15min.csv` với các cột `cluster_id`, `timestamp_utc`, `occupancy_ports`, `session_arrivals`; `outputs/nv5/baseline_predictions.csv` có `cluster_id`, `timestamp_utc`, `target`, `model`, `split`, `y_true`, `y_pred`; bảng metric chứa MAE, RMSE, R² riêng theo mục tiêu, cụm và validation/test. Kỳ có thể dùng bảng dự đoán để chạy thêm Robustness Checks.

Cell audit đọc `sessions_features.parquet`: 259.356 phiên hợp lệ, trong đó 12 phiên thời lượng bằng 0 bị loại khỏi chuỗi; 139 cách ghi `port_id` gốc chuẩn hóa thành 117 ID cổng. Lần chạy hiện tại có 9 cụm × 2 mục tiêu × 7 mô hình × 3 giai đoạn = 378 dòng metric. Bảng metric đầy đủ ở `outputs/nv5/nv5_model_comparison.csv`; dự báo ở `outputs/nv5/baseline_predictions.csv`; audit chuỗi ở `outputs/nv5/data_audit.json`.

Trung bình theo 9 cụm trên **test nửa cuối 2019**: với occupancy, XGBoost có MAE 0,2703 cổng, RMSE 0,4650, R² 0,9131; Random Forest có 0,2796/0,4703/0,9117; baseline `t-1` có 0,2148/0,4883/0,9045. XGBoost giảm RMSE so với `t-1` khoảng 4,8% nhưng MAE cao hơn khoảng 25,9%; không thể kết luận XGBoost tốt nhất theo mọi thước đo. Với arrivals, XGBoost có MAE 0,2141 phiên, RMSE 0,3625, R² 0,2165; Random Forest có 0,2206/0,3635/0,2120. R² arrivals thấp cho thấy khả năng giải thích biến động theo khung 15 phút còn hạn chế.

Trên **stress 2020**, occupancy XGBoost có MAE/RMSE 0,1473/0,3226, trong khi `t-1` là 0,0996/0,3226; dự báo `t-1` tốt hơn về MAE và gần bằng về RMSE. Với arrivals, Ridge có RMSE 0,2419 so với XGBoost 0,2463. Vì vậy không nên khẳng định XGBoost ổn định vượt mọi baseline khi điều kiện vận hành thay đổi. Các chỉ số trên là trung bình đều theo cụm, không phải metric gộp theo mọi timestamp.

Chạy test:

```bash
python -m pytest tests/test_nv5_forecasting.py -q
```

### Lưu ý diễn giải kết quả

Baseline `t-1` được thêm theo đề cương. Điểm MAE và RMSE có thể xếp mô hình khác nhau; cần trình bày cả hai thay vì chỉ tuyên bố một mô hình thắng chung. Giới hạn cổng vật lý tính từ toàn bộ giai đoạn chỉ dùng trong audit, không dùng để chặn dự báo khi đánh giá vì lịch sử công suất hoạt động theo thời điểm chưa được xác định. Dự báo chỉ được chặn dưới ở 0. Random Forest là mô hình đối chiếu bổ sung, còn XGBoost vẫn là mô hình chính theo proposal.

Các biểu đồ PNG và file `*_metrics.csv` có thời điểm cũ hơn bảng metric hiện hành; chưa được tạo lại trong lần chạy này. Dùng `nv5_model_comparison.csv` cho kết luận hiện tại.
