# Rà soát phương pháp NV5 — 19/11/2026

Notebook thực thi: `notebooks/05_NV5_demand_forecasting.ipynb`.

## Kết luận về phương pháp

Hồi quy có giám sát với lag, rolling và lịch là thiết kế phù hợp cho **dự báo một khung 15 phút tiếp theo**, với điều kiện đã có quan sát mục tiêu đến hết khung trước. Đây không phải dự báo cả ngày tại một thời điểm xuất phát. Khi đánh giá một bước, dùng quan sát thật của các khung test đã qua để tạo lag không phải rò rỉ tương lai. Không được diễn giải như dự báo nhiều bước không có cập nhật quan sát.

Độ nhanh không phải tiêu chí đúng/sai. Histogram boosting, cây nông, số đặc trưng nhỏ và nhiều đoạn chuỗi bằng 0 có thể làm fit nhanh. Bằng chứng cần xem là số dòng thực sự được fit, cấu hình, thời gian từng lần fit, kiểm tra chống rò rỉ và khả năng vượt baseline.

## Những lỗi đã sửa

- Notebook cũ khác mô tả báo cáo: thiếu baseline t−1, thiếu stress test và chưa chọn siêu tham số bằng validation. Đã thêm cả ba.
- Ridge chọn alpha trong 0,1/1/10/100; XGBoost chọn 100 cây sâu 3 hoặc 160 cây sâu 4, learning rate 0,05 bằng RMSE validation. Random Forest dùng 60 cây, sâu 12, tối thiểu 4 quan sát/lá.
- Đã thêm lag 2, rolling 12 khung, năm và chỉ báo chính sách theo thiết kế. Lịch dùng giờ Palo Alto có DST; lưới và ranh giới chia dùng UTC. Việc sửa lịch có thể làm kết quả mới khác báo cáo cũ.
- Không chặn dự báo bằng số cổng quan sát từ toàn bộ lịch sử vì đó không phải sức chứa khả dụng tại thời điểm dự báo. Chỉ chặn dưới tại 0.
- Tách tổng hợp có/không có chuỗi mục tiêu hằng, tránh R²=1 theo quy ước thư viện làm tăng trung bình.
- Kiểm tra định danh cổng sau chuẩn hóa; gán cụm theo vị trí từng phiên để xử lý cổng chuyển địa điểm.
- Mỗi lần chạy notebook tạo thư mục kết quả riêng; xuất candidate validation, cấu hình được chọn, thời gian và manifest để truy vết. Sửa các đoạn giải thích bị lỗi mã hóa.

## Bằng chứng kiểm chứng

- 18 test tự động qua: giao khoảng `[start,end)`, đếm một lần/cổng/khung, tách cụm, ranh giới tập, scaler train-only, lag/rolling chỉ nhìn quá khứ, lịch địa phương và thay đổi test không làm đổi kết quả validation dùng chọn cấu hình.
- Kiểm tra độc lập trên dữ liệu thật: 108 khung ngẫu nhiên thuộc chín cụm đều có occupancy/arrivals khớp cách lọc trực tiếp từng khoảng phiên. Bộ sinh chuỗi có 2.978.280 dòng (330.920 khung/cụm), 259.344 phiên và 117 cổng; không thiếu định danh ở các phiên hợp lệ.
- Lượt chạy đầy đủ được lưu tại `outputs/nv5/method_audit_20261119/`. Chỉ công bố metric sau khi đủ hai mục tiêu × chín cụm × bảy mô hình × ba giai đoạn = 378 dòng.

## Giới hạn chưa thể giải quyết bằng mã hiện tại

1. **Không biết lịch khả dụng:** số 0 nghĩa là không có phiên được ghi nhận, chưa xác nhận trạm mở cửa, đã được lắp đặt hay dữ liệu thu thập đầy đủ. SHERMAN và các giai đoạn trước khi trạm có hoạt động cần đọc riêng. Cần lịch thiết bị và dữ liệu trạng thái để đánh giá sử dụng sức chứa thực.
2. **Định nghĩa occupancy:** đếm các cổng có phiên giao với toàn khung; không đồng nghĩa số cổng đồng thời bị giữ tại một thời điểm. Không suy diễn thành công suất điện.
3. **Quan sát thời gian thực:** dữ liệu lịch sử có giờ kết thúc nhưng không chứng minh hệ thống cung cấp trạng thái ngay sau mỗi 15 phút. Phải kiểm chứng độ trễ nếu triển khai.
4. **Phạm vi đánh giá theo thời gian:** test chính và stress 2020 bao phủ hai giai đoạn cụ thể. Bổ sung hai cửa sổ đánh giá lịch sử cho occupancy ở phần kiểm chứng bên dưới. Chưa có khoảng tin cậy cho chênh lệch sai số.
5. **Baseline mạnh:** R² cao có thể chủ yếu đến từ occupancy bền qua nhiều khung. Phải báo MAE/RMSE và mức cải thiện so với t−1; arrivals nhiều số 0 cần thêm đối chứng dự báo 0 khi đánh giá tính hữu ích vận hành.

Kiểm tra trực tiếp trên tám cụm test có hoạt động: 79,09% khung occupancy giữ nguyên, 85,54% khung arrivals bằng 0. Dự báo arrivals luôn bằng 0 có MAE trung bình 0,1716 và RMSE trung bình 0,4698 phiên/khung. Đây là đối chứng chẩn đoán bổ sung, không nằm trong bảy mô hình của bảng chính. Nếu MAE là mục tiêu ưu tiên duy nhất, mô hình học máy cần chứng minh tốt hơn cả đối chứng này; không chỉ so với Historical Mean. Khả năng phát hiện khung có xe đến cần đánh giá theo mục tiêu cảnh báo riêng.

## Đối chiếu báo cáo

### Kết quả chạy lại đã kiểm tra

Đã xuất đủ **378 dòng metric**, 126 lần fit cấu hình (72 Ridge, 18 Random Forest, 36 XGBoost). Tổng thời gian fit và dự báo validation là **486,79 giây (~8,1 phút)**, chưa tính đọc dữ liệu, tạo chuỗi và xuất CSV. XGBoost mất 1,05–4,21 giây/lần fit và validation (trung vị 2,08 giây); Random Forest trung vị 21,50 giây. Điều này xác nhận fit XGBoost vài giây là có thể xảy ra trên thiết kế này. Không fit lại mô hình sau mỗi khung 15 phút; dự báo được tính theo lô từ đặc trưng chỉ có dữ liệu quá khứ.

Test 2019, trung bình đều trên **tám cụm có mục tiêu không hằng**:

| Mục tiêu / mô hình | MAE | RMSE | R² |
|---|---:|---:|---:|
| Occupancy / t−1 | 0,2416 | 0,5493 | 0,8926 |
| Occupancy / XGBoost | 0,3043 | 0,5234 | 0,9022 |
| Arrivals / Historical Mean | 0,2178 | 0,4289 | 0,0370 |
| Arrivals / Random Forest | 0,2438 | 0,4073 | 0,1188 |
| Arrivals / XGBoost | 0,2395 | 0,4076 | 0,1189 |

Occupancy XGBoost giảm RMSE khoảng **4,72%** so với t−1, nhưng MAE cao hơn khoảng 26%. **Random Forest nhỉnh hơn XGBoost về RMSE arrivals ở mức tổng hợp**; không giữ nguyên kết luận XGBoost tốt nhất của lượt cũ.

Stress 2020: XGBoost có occupancy RMSE **0,322145**, thấp hơn một chút so với **0,322563** của t−1, nhưng MAE cao hơn (0,1462 so với 0,0996). Không giữ câu cũ “t−1 đạt cả MAE và RMSE tốt nhất” cho lượt mới. Arrivals vẫn có RMSE thấp nhất ở Ridge (**0,2419**, so với XGBoost **0,2438**). Chênh lệch RMSE occupancy rất nhỏ, chưa chứng minh có ý nghĩa thống kê.

File kiểm chứng: `validation_candidates.csv`, `model_timings.csv`, `nv5_model_comparison.csv`, `summary_all_clusters.csv`, `summary_nonconstant_clusters.csv`, `baseline_predictions.csv`, `target_diagnostics.csv`, `data_audit.json`, `run_manifest.json` trong thư mục lượt chạy mới. Đã qua **18 kiểm tra tự động**. Cuối lượt chạy có lỗi tra tên distribution `xgboost` khi máy cài `xgboost-cpu`; model và bảng dự đoán/metric đã được ghi xong. Đã sửa logger dùng phiên bản module thực và hoàn thiện manifest/summary từ kết quả đã lưu, không huấn luyện lại hoặc thay đổi dự đoán.

Các số ở mục 4.5 cũ là kết quả được báo cáo của lượt chạy trước, không mặc định là kết quả của notebook đã sửa. Cần đối chiếu toàn bộ bảng/biểu đồ từ cùng một lượt chạy mới; không lựa số tốt hơn giữa hai lượt. Gain không chứng minh tác động nhân quả hay mức giảm sai số khi bỏ đặc trưng.

## Kiểm chứng bổ sung cho NV5

Chạy từ gốc repo với thư mục kết quả của NV5. Báo cáo bổ sung nằm trong thư mục con `robustness/`.

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_nv5_robustness.py outputs/nv5/method_audit_20261119
```

**Occupancy.** Ở mỗi cửa sổ, XGBoost fit lại trên train của từng cụm, chọn giữa hai cấu hình hiện có bằng RMSE validation, rồi so với persistence t−1 trên các khung test trùng nhau. Mốc chia tính theo UTC.

| Test | Train đến hết | Validation |
|---|---|---|
| Nửa cuối 2018 | 2017 | Nửa đầu 2018 |
| Nửa đầu 2019 | Nửa đầu 2018 | Nửa cuối 2018 |

Hai kỳ test bổ sung không giao nhau với kỳ test chính nửa cuối 2019, nhưng có thể trùng với dữ liệu train/validation của thiết kế chính. Đây là kiểm chứng hồi cứu, với cấu hình đã định trước cho lần kiểm chứng này. Chỉ số tính riêng theo cụm, rồi lấy trung bình đều trên các cụm có mục tiêu không hằng trong mỗi kỳ.

| Kỳ test | Số cụm | MAE t−1 | MAE XGBoost | RMSE t−1 | RMSE XGBoost | Thay đổi RMSE của XGBoost |
|---|---:|---:|---:|---:|---:|---:|
| Nửa cuối 2018 | 8 | 0,2238 | 0,3604 | 0,5236 | 0,6816 | Tăng 30,16% |
| Nửa đầu 2019 | 8 | 0,2413 | 0,2985 | 0,5458 | 0,5179 | Giảm 5,11% |
| Nửa cuối 2019 (test chính) | 8 | 0,2416 | 0,3043 | 0,5493 | 0,5234 | Giảm 4,72% |

Nửa cuối 2018, XGBoost giảm RMSE ở sáu cụm nhưng tăng mạnh tại CAMBRIDGE (0,640 → 1,117) và TED THOMPSON (0,490 → 1,427). Hai cụm này kéo RMSE trung bình của XGBoost lên trên t−1. Nửa đầu 2019, XGBoost giảm RMSE ở cả tám cụm. Persistence t−1 có MAE trung bình thấp hơn trong cả ba kỳ. Kết quả ủng hộ lợi thế RMSE của XGBoost trong năm 2019 và cho thấy lợi thế thay đổi theo kỳ và theo cụm. Hai cửa sổ bổ sung fit 36 cấu hình XGBoost, mất tổng cộng 88,1 giây gồm fit và dự báo validation.

**Arrivals.** Chấm lại dự báo đã lưu của kỳ test nửa cuối 2019 trên tám cụm có hoạt động. Dự báo luôn 0, Historical Mean, Random Forest và XGBoost được chấm trên cùng các khung. Nhóm 0/1/≥2 xác định từ số phiên quan sát được, dùng để chẩn đoán sai số sau khi có kết quả thực tế.

| Số phiên thực tế | Số khung | MAE luôn 0 | MAE Historical Mean | MAE Random Forest | MAE XGBoost |
|---|---:|---:|---:|---:|---:|
| 0 | 120.877 | 0,0000 | 0,0812 | 0,1446 | 0,1344 |
| 1 | 17.178 | 1,0000 | 0,8511 | 0,7016 | 0,7227 |
| ≥2 | 3.257 | 2,1217 | 1,9574 | 1,7646 | 1,7955 |
| Toàn bộ | 141.312 | 0,1716 | 0,2178 | 0,2438 | 0,2395 |

Baseline 0 đạt MAE toàn kỳ thấp nhất trong bảng vì đa số khung không có phiên. Random Forest và XGBoost giảm sai số ở các khung có phiên, nhưng dự báo thấp ở nhóm ≥2. RMSE toàn kỳ tương ứng là 0,4698 cho baseline 0, 0,4289 cho Historical Mean, 0,4073 cho Random Forest và 0,4076 cho XGBoost.

Tham khảo phương pháp: [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), [XGBoost histogram tree method](https://xgboost.readthedocs.io/en/stable/treemethod.html).
