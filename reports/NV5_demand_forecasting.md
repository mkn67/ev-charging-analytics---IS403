# NV5 — Dự báo occupancy cổng và session arrivals (mục 3.5.1–3.5.2)

## 3.5.1. Định nghĩa mục tiêu và tạo chuỗi 15 phút

NV5 tạo chuỗi theo từng **cụm trạm** `cluster_id` đã được nhóm phê duyệt. Một cluster là đơn vị nhóm trạm do nhóm định nghĩa; không suy ra `cluster_id` từ tên trạm, số hiệu cổng hay cluster hành vi phiên của NV2. NV2 hiện phân cụm **phiên sạc theo hành vi**, không cung cấp mapping cụm trạm cho NV5. Vì vậy thí nghiệm theo cụm chưa được chạy cho tới khi nhóm hoàn tất `port_id,cluster_id` trong mapping.

`port_id` của NV1 được tạo từ `MAC Address` và `Port Number` theo dạng `{MAC Address}_Port_{Port Number}`. Dữ liệu hiện có 139 `port_id`; mỗi ID ánh xạ duy nhất tới một cặp MAC/cổng, không có cặp nào sinh nhiều ID. NV5 kiểm tra lại quan hệ này khi nạp dữ liệu. Nếu thiếu một thành phần định danh, NV1 để `port_id` rỗng thay vì tạo chuỗi giả như `nan_Port_nan`.

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

Mọi baseline được fit/tính **riêng theo `cluster_id`**. Giao diện nhận các mốc train, validation, test do Khải/nhóm cung cấp; chương trình không tự chia 80/20. Các mốc là ranh giới kết thúc loại trừ (`train_end_utc`, `validation_end_utc`, `test_end_utc`) trong JSON.

- **Historical Mean:** trung bình mục tiêu của train theo thứ trong tuần và slot 15 phút, riêng từng cluster. Nếu một slot chưa xuất hiện trong train, dùng trung bình train của cluster đó.
- **Persistence Day (`t-96`)** và **Persistence Week (`t-672`):** lấy giá trị lịch sử cùng cluster, không trộn giữa các cluster.
- **Ridge:** scaler được fit chỉ trên train của cluster; cùng scaler transform validation/test. Không fit lại scaler trên validation/test.
- **Random Forest, XGBoost:** fit trên train của cluster. Đây là đối chứng mô hình; metric được xuất riêng cho validation và test.
- **Persistence `t-1`:** đối chứng được đề xuất để nhóm cân nhắc mở rộng proposal, không phải lỗi thiếu của phân công hiện tại; chưa đưa vào bảng chính khi chưa có đồng thuận.

Đánh giá là one-step-ahead: các lag trong validation/test dùng quan sát quá khứ đã có tại thời điểm dự báo. Kết quả của lượt cũ dùng một chuỗi toàn mạng và split tự đặt không còn đại diện cho thiết kế theo cụm; cần chạy lại sau khi nhận mapping và mốc chia từ nhóm. Vì hai đầu vào này chưa có trong repo, báo cáo này không giữ các metric cũ như kết quả bàn giao.

### Đầu vào bắt buộc từ nhóm

1. CSV mapping có đúng hai cột `port_id,cluster_id`, một dòng cho mỗi cổng vật lý quan sát. Mẫu 139 cổng nằm ở `reports/station_cluster_map_template.csv`; sao chép mẫu thành `data/processed/station_cluster_map.csv` rồi điền cluster theo quyết định của nhóm. Notebook từ chối ID trùng, cổng không tồn tại hoặc cổng chưa được gán cụm.
2. JSON mốc thời gian theo định dạng, ví dụ cấu trúc sau (giá trị phải do Khải/nhóm cung cấp; không dùng các chuỗi minh họa làm mốc chạy):

```json
{
  "train_end_utc": "<UTC timestamp>",
  "validation_end_utc": "<UTC timestamp>",
  "test_end_utc": "<UTC timestamp>"
}
```

Toàn bộ mã NV5 được đặt trong `notebooks/05_NV5_demand_forecasting.ipynb`; thư mục `scripts/` chỉ chứa script chương 4. Mở notebook, chạy lần lượt các cell định nghĩa rồi chạy cell cuối sau khi điền hai đầu vào. Có thể chạy notebook bằng Jupyter từ thư mục gốc repo.

### Bảng bàn giao và kiểm tra

Notebook xuất `outputs/nv5/timeseries_15min.csv` với các cột `cluster_id`, `timestamp_utc`, `occupancy_ports`, `session_arrivals`; `outputs/nv5/baseline_predictions.csv` có `cluster_id`, `timestamp_utc`, `target`, `model`, `split`, `y_true`, `y_pred`; bảng metric chứa MAE, RMSE, R² riêng theo mục tiêu, cụm và validation/test. Kỳ có thể dùng bảng dự đoán để chạy thêm Robustness Checks.

Cell kiểm tra dữ liệu chạy được trước khi có mapping và mốc chia; nó hiển thị kết quả NV1 trong notebook và lưu `outputs/nv5/nv5_input_audit.json`. Lần kiểm tra hiện tại đọc `sessions_features.parquet`: 259.356 phiên hợp lệ, 12 phiên thời lượng bằng 0, 139 cổng quan sát, không thiếu `port_id`, không lệch định danh MAC/cổng. `cluster_map_ready=False` và chưa có file mốc chia nên chưa có kết quả dự báo. Khi chạy mô hình, `outputs/nv5/data_audit.json` ghi số phiên được giữ, số khoảng không dương bị loại, cổng/cluster và giới hạn occupancy; nếu occupancy vượt số cổng vật lý quan sát được trong cụm, pipeline dừng lỗi. Test đọc và kiểm tra trực tiếp các cell định nghĩa trong notebook; gồm hai phiên cùng cổng, nhiều cổng đồng thời, kết thúc đúng biên, zero-fill, missing `port_id`, tính riêng theo cụm và kiểm tra ID/map.

Chạy test:

```bash
python -m pytest tests/test_nv5_forecasting.py -q
```
