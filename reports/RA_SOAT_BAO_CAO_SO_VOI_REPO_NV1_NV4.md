# Rà soát IS403.pdf so với repository — NV1 đến NV4

Ngày rà soát: 11/11/2026. Nguồn đối chiếu: `IS403.pdf` (131 trang), `Khác biệt giữa repository và báo cáo.pdf` (4 trang), mã/notebook và các bảng kết quả hiện có trong workspace. Phần đối chiếu PDF bên dưới ghi nhận hiện trạng lúc rà soát. Sau đó đã chạy lại NV1–NV4 và áp dụng một số cải tiến mã; xem mục **Cập nhật triển khai** ở cuối. PDF gốc chưa được sửa, nên các đề xuất chỉnh báo cáo vẫn còn hiệu lực.

## Kết luận cần xử lý trước

1. **Không dùng một mẫu “NV1 → NV4” duy nhất.** NV1 có 259.356 phiên theo `is_valid_session`; notebook NV2 tự lọc còn 258.720; NV4 lọc thêm kiểm tra timestamp còn 258.875, trong đó 258.836 phiên thuộc 33 trạm đủ điều kiện xếp hạng. Báo cáo đang gọi 258.720 là dữ liệu sạch chung.
2. **Chọn nguồn kết quả NV2.** Notebook NV2 hiện lưu kết quả trên 258.720 phiên, trong khi `outputs/tables/kmeans_*.csv` hiện có kết quả trên 259.356 phiên và nhãn cụm khác. Không ghép chỉ số từ nguồn này với hồ sơ cụm từ nguồn kia.
3. **NV3 cần trình bày kết quả suy luận hiện hành.** Code dùng cluster bootstrap theo User ID, 2.000 lần, và Holm; riêng Energy có CI bootstrap chứa 0 dù p-value Mann–Whitney rất nhỏ. Báo cáo không nên diễn giải p-value Mann–Whitney là bằng chứng độc lập hoặc nhân quả.
4. **NV4 cần cập nhật bảng số và hoàn thiện TOPSIS.** Ma trận 33 × 6 còn đúng; số phiên, ma trận, trọng số, xếp hạng và độ nhạy phải lấy từ cùng một lượt chạy. Thân `IS403.pdf` dừng ở mục 3.4.2, chưa có nội dung 3.4.3 dù mục lục có.

## NV1 — Chương 2.2–2.3 (PDF trang 37–46)

| Mục | Trong PDF | Repository hiện tại | Đề xuất sửa |
|---|---|---|---|
| Mẫu sạch, bảng 2.2.4 | 258.720 phiên, ghi 99,98%, gọi là tập chuẩn cho NV1→NV4 | `outputs/tables/data_quality_audit_summary.csv`: 259.415 gốc, 4 trùng, 45 lỗi thời lượng, 10 cờ công suất, **259.356 phiên hợp lệ** = 99,98% của 259.415. 258.720/259.415 ≈ **99,73%**. | Đổi dòng kết quả NV1 thành 259.356/99,98%; thêm bảng đối soát mẫu riêng cho NV2, NV3, NV4. Không cộng 45 và 10 nếu chưa chứng minh hai cờ không giao nhau; lấy trực tiếp `is_valid_session`. |
| Công suất | Bảng 2.2.4 ghi `Pavg > 7,2 kW` loại 10 phiên | `src/config.py` và `src/data_validation.py` dùng giới hạn theo `Port Type`: Level 1 = 1,92 kW; Level 2/default = 22 kW. 7,2 kW là mức danh định Level 2, không phải ngưỡng cờ hiện dùng. | Đổi nhãn thành `Pavg > Pmax(Port Type)`, ghi các ngưỡng và nêu 10 là số **gắn cờ**; diễn giải việc loại trong từng tập phân tích. |
| IQR khảo sát gốc, mục 2.2.2 | Tổng 5,967 h/12.678; sạc 5,180 h/5.492; điện 22,966 kWh/8.656 | Tính trực tiếp trên **259.415 dòng CSV gốc**: tổng **5,969 h/12.763**, sạc **5,183 h/5.518**, điện **22,970 kWh/8.696**. | Thay bảng khảo sát gốc bằng các giá trị này. Ghi rõ số đếm dùng hàng rào chưa làm tròn. |
| Cờ IQR trong NV1 | PDF xem như cùng phép tính với bảng khảo sát gốc | `build_clean_pipeline` loại trùng rồi tính Q1/Q3 trên 259.366 dòng không lỗi logic thời lượng, nhưng gắn cờ cho toàn bộ 259.411 dòng sau bỏ trùng. Audit đang ghi 12.763 cờ tổng thời gian, **8.697 cờ điện năng**; cờ thời gian sạc tính từ parquet là 5.519. | Tách rõ bảng “khảo sát CSV gốc” và bảng “cờ NV1 sau tiền xử lý”, nêu mẫu tính Q1/Q3 và mẫu được gắn cờ. PDF sai khác 4 trang ghi 8.696 là đúng cho CSV gốc, **không thay** cho 8.697 trong audit NV1. |
| Mục 2.3 | Trình bày Useful Charge Ratio, sin/cos, lag và rolling như đã được tạo trong dữ liệu chuẩn bị chung | `src/feature_engineering.py` tạo idle time/ratio và biến lịch cơ bản cho parquet NV1; không tạo đủ Useful Charge Ratio, sin/cos, lag/rolling. Các biến sau được tạo trong phân tích từng nhiệm vụ, đặc biệt notebook NV5. | Giữ công thức như thiết kế phương pháp nhưng đổi câu chữ thành “được tạo tại bước NV tương ứng”; liệt kê cột thực có trong `sessions_features.parquet`. |

Các số 181 phiên chồng lấn cổng và 0 phiên zero-energy trong PDF khớp audit hiện tại. Kiểm tra lại chú thích “loại” với quy trình thực tế: NV1 giữ bản ghi sau bỏ trùng, gắn cờ lỗi và dùng `is_valid_session` để chọn mẫu phân tích.

## NV2 — Chương 3.2 (PDF trang 76–100)

**Nguồn kết quả được đề xuất cho bản báo cáo hiện hành:** output lưu trong `notebooks/02_NV2_occupancy_clustering.ipynb` vì notebook này chạy trên 258.720 phiên và là nguồn của phần lớn bảng 3.1–3.8. Không lấy `outputs/tables/kmeans_cluster_profiles.csv` để thay một phần bảng: file đó có tổng 259.356 phiên, nhóm kích thước 67.981/150.913/33.195/7.267 và nhãn cụm khác.

| Mục | Trong PDF | Notebook NV2 hiện tại | Đề xuất sửa |
|---|---|---|---|
| Mẫu, 3.2.1 | 258.720 là tập hợp lệ lấy trực tiếp từ NV1 | Notebook tự đọc CSV, bỏ trùng, áp dụng điều kiện thời lượng/điện năng, ngưỡng công suất **19,2 kW**, rồi kiểm tra lệch timestamp ≤59 giây; còn 258.720. NV1 dùng ngưỡng theo Port Type, Level 2 = 22 kW. | Viết “mẫu NV2 được lọc bổ sung từ dữ liệu gốc theo quy tắc riêng”; trình bày flow 259.415 → 259.411 → 259.366 → 259.356 → 258.720 và lý do ngưỡng 19,2 kW khác NV1. Nếu muốn gọi là kế thừa NV1, sửa code để bắt đầu từ parquet NV1 rồi chạy lại toàn bộ NV2. |
| Bảng 3.1, 3.4 | Silhouette 0,469; DBI 0,752; CH 7.457; WCSS k=4 là 248.489 | Notebook lưu **0,473 / 0,730 / 8.122**, WCSS **248.145**. | Cập nhật bảng và nhận xét chọn k trên cùng lần chạy; không thay riêng từng số. |
| Hình 3.3, hồ sơ cụm | Kích thước sắp giảm: 155.576; 91.112; 6.913; 5.755 (tổng 259.356); nhóm nhàn rỗi có giờ đến trung vị ~5:00 | 155.185; 90.894; 6.913; 5.728 (tổng 258.720). Nhóm nhàn rỗi dài trong notebook có giờ đến trung vị **20,2 giờ**, khoảng 20:12 theo giờ địa phương. | Tạo lại hình và đoạn mô tả; đối chiếu cụm theo **hồ sơ hành vi**, không theo số nhãn cluster vì nhãn K-Means có thể hoán đổi. |
| Bảng 3.5–3.6 DBSCAN | ε=0,5/MinPts=10 có 4 cụm; 13/18 cấu hình chỉ có 1 cụm; mẫu con 3/3/1/2/5 | Bảng output trong notebook cho ε=0,5/10 có **2 cụm**; đếm bảng lưới có **11/18** cấu hình 1 cụm; năm mẫu con có **2/1/2/2/1** cụm. Ngay phần nhận xét Markdown trong notebook vẫn ghi 13/18, mâu thuẫn với bảng output. | Sửa báo cáo theo bảng notebook và sửa luôn lời nhận xét trong notebook; ghi rõ cách đếm cụm không tính noise `-1`. |
| Split-half | 129.678 phiên/nửa; ARI/NMI/accuracy = 0,9966/0,9912/99,90% | 129.360 phiên/nửa; **0,9948/0,9864/99,84%**. Notebook còn kiểm tra dùng chung scaler: ARI 0,9986, NMI 0,9939. | Cập nhật và phân biệt kiểm tra gốc với kiểm tra shared scaler; nêu hai cách nếu dùng cả hai. |
| Bảng 3.2, 3.8, theo năm | Một số số thuộc mẫu 259.356 | Notebook NV2 dùng 258.720; năm 2017 = 48.857, năm 2020 = 20.064. | Tạo lại tất cả bảng/hình mô tả từ cùng mẫu và ghi N trên từng bảng. Chỉ mô tả thay đổi trước/sau; không gọi là tác động nhân quả của chính sách. |

## NV3 — Chương 3.3 (PDF trang 101–118)

Phần định nghĩa giai đoạn và phân khúc người dùng tương đối gần code. Các sửa quan trọng nằm ở phương pháp suy luận và bunching.

| Mục | Trong PDF | Notebook/output hiện tại | Đề xuất sửa |
|---|---|---|---|
| 3.3.3 | Mô tả chủ yếu Mann–Whitney U, Cliff's Delta và quy tắc p<0,05 | Notebook tính **cluster bootstrap theo User ID, 2.000 lần**, CI 95% cho Delta, đồng thời hiệu chỉnh **Holm** cho bốn metric. Các phiên cùng người dùng không độc lập. | Trình bày bootstrap/Holm là phần kiểm chứng chính; p-value Mann–Whitney chỉ tham khảo. Báo cáo Delta, CI và số user cùng N phiên. Không diễn giải khác biệt Pre/Post là tác động nhân quả. |
| Kết quả Energy | Dễ kết luận có khác biệt vì p-value rất nhỏ | `3.3.3_stats.csv`: Energy Delta −0,0281; CI bootstrap **[−0,061; 0,002]** chứa 0; p-value MWU 2,46×10⁻³⁴. | Ghi rõ hai cách đánh giá cho tín hiệu khác nhau; chưa gọi kết quả Energy là vững theo CI bootstrap. Cột Holm trong file áp dụng lên p-value MWU, không thay cho kiểm định bootstrap. |
| 3.3.4 | Mô tả cả ngưỡng 20 phút và 180 phút; công thức `max(0, Ttotal−Tcharging)`; biểu đồ idle 0–40 phút, chỉ số tỷ lệ trong cửa sổ đối xứng | Code hiện chỉ kiểm tra **20 phút**, giữ thời lượng lỗi ở dạng thiếu/loại theo điều kiện phân tích, vẽ idle **0–60 phút**, so hai dải **[15,20)** và **[20,25)**, tính `Bunching_Ratio`. `3.3.4_bunching.csv`: Pre 0,991; Post 1,156. | Sửa mục 3.3.4 theo phép tính đã chạy; bỏ phần 180 phút hoặc triển khai thêm phân tích 180 phút rồi tái tạo kết quả. Không mô tả giá trị lỗi bị ép về 0. Chỉ diễn giải đây là mô tả gần ngưỡng, chưa chứng minh né phí. |

## NV4 — Chương 3.4 (PDF trang 119–128)

| Mục | Trong PDF | Repository hiện tại | Đề xuất sửa |
|---|---|---|---|
| 3.4.1, mẫu | 258.720 phiên NV4; 258.681 phiên ở 33 trạm; HAMILTON #2 có 23.666 phiên | `outputs/nv4_run_metadata.json`: **258.875** phiên hợp lệ NV4; **258.836** phiên thuộc 33 trạm đủ điều kiện; 46 tên trạm sau chuẩn hóa. `outputs/nv4_station_criteria.csv`: HAMILTON #2 **23.682** phiên. | Thay phần mô tả mẫu và toàn bộ ma trận/bảng thống kê 33 × 6 từ cùng lượt chạy; giải thích NV4 loại thêm 481 phiên theo kiểm tra timestamp so với NV1. |
| Bảng 3.12, trọng số | C1 = 0,2939; C5 = 0,0656 | `outputs/nv4_criteria_weights.csv`: C1 **0,2944**, C2 0,2777, C5 **0,0651**, C6 0,0555 (làm tròn 4 chữ số). | Thay bảng, đồ thị trọng số và câu diễn giải liên quan; kiểm tra mọi số ở Bảng 3.12 từ CSV, không chép từng ô theo PDF sai khác. |
| 3.4.2, công thức | Viết chuẩn hóa Min–Max “không tham gia vào hàm khoảng cách Euclid” | `src/topsis.py`: TOPSIS tính khoảng cách Euclid trên ma trận **đã chuẩn hóa và gán trọng số**. | Sửa thành: Min–Max đưa các tiêu chí về thang [0,1]; ma trận chuẩn hóa được nhân trọng số, rồi dùng trong khoảng cách tới lý tưởng dương/âm. |
| 3.4.3 và độ nhạy | Có trong mục lục nhưng thiếu nội dung thân báo cáo; chưa diễn giải đầy đủ S0–S6 | `outputs/nv4_topsis_rankings.csv` và `outputs/nv4_sensitivity_analysis.csv` đã có 33 trạm, hai bộ trọng số và 7 kịch bản. | Viết mục 3.4.3 từ `reports/NV4_section_3_4_3.md` sau khi đối chiếu số mới; trình bày top/bottom theo Entropy, thay đổi khi dùng trọng số đều và độ nhạy S0–S6. |
| Đánh số hình | Hình 3.5 và 3.6 xuất hiện ở cả NV3 và NV4 | PDF có hai cặp chú thích trùng | Đánh lại số hình và cập nhật mọi tham chiếu trong thân bài, danh mục hình. |

Ma trận **33 trạm × 6 tiêu chí** trong PDF vẫn đúng về cấu trúc. `C5_ty_le_nhan_roi` trong code là **trung bình Idle Ratio từng phiên** theo trạm; `C5_weighted` được tính riêng nhưng không đưa vào ma trận TOPSIS. Khi sửa báo cáo phải giữ đúng định nghĩa C5 đang được xếp hạng, hoặc đổi thiết kế và chạy lại toàn bộ NV4.

## Thứ tự sửa đề xuất

1. **Chốt nguồn và mẫu cho từng NV** bằng một bảng đối soát: dữ liệu gốc, bỏ trùng, NV1-valid, NV2-valid, NV3-valid theo từng metric, NV4-valid, trạm đủ điều kiện. Ghi rõ mỗi bảng/hình dùng mẫu nào. Quyết định có giữ bộ lọc NV2 riêng 19,2 kW hay chuyển NV2 về pipeline NV1; nếu đổi code, phải chạy lại và thay toàn bộ kết quả NV2.
2. **Khóa một lượt chạy chuẩn** cho NV1–NV4 (commit code, phiên bản dữ liệu, tham số và ngày chạy). NV2 cần xuất lại bảng/hình từ chính notebook hiện hành hoặc sửa notebook để dùng bảng output chuẩn; không trộn `outputs/tables/kmeans_*.csv` với notebook 258.720 phiên.
3. **Sửa Chương 2**: 259.356/99,98%, ngưỡng công suất theo Port Type, hai tầng IQR, vị trí tạo đặc trưng.
4. **Sửa Chương 3.2**: thay trọn Bảng 3.1–3.8, Hình 3.3 và các đoạn diễn giải từ cùng lượt NV2; sửa câu 13/18 trong notebook.
5. **Sửa Chương 3.3**: mô tả bootstrap/Holm; phân biệt tín hiệu MWU và CI bootstrap; đồng bộ bunching chỉ quanh 20 phút theo code, trừ khi nhóm thật sự triển khai 180 phút.
6. **Sửa Chương 3.4**: cập nhật mẫu/ma trận/trọng số, hoàn thiện 3.4.3 từ kết quả mới, giải thích độ nhạy và đánh lại số hình.
7. **Kiểm tra chéo cuối**: mọi N, bảng, hình và câu kết luận trong PDF phải truy được tới một artifact/cell của cùng lượt chạy. Xuất lại PDF rồi kiểm tra mục lục, chú thích và số hình.

## Tệp bằng chứng chính trong repo

- NV1: `src/config.py`, `src/feature_engineering.py`, `src/data_validation.py`, `outputs/tables/data_quality_audit_summary.csv`, `data/processed/sessions_clean.parquet`.
- NV2: `notebooks/02_NV2_occupancy_clustering.ipynb`; **không coi** `outputs/tables/kmeans_*.csv` hiện tại là cùng lượt chạy với notebook.
- NV3: `notebooks/03_NV3_policy_evaluation.ipynb`, `notebooks/outputs_nv3_v6/3.3.3_stats.csv`, `3.3.4_bunching.csv`.
- NV4: `src/nv4_analysis.py`, `src/topsis.py`, `outputs/nv4_run_metadata.json`, `nv4_station_criteria.csv`, `nv4_criteria_weights.csv`, `nv4_topsis_rankings.csv`, `nv4_sensitivity_analysis.csv`.

## Cải tiến mã và phương pháp sau khi đồng bộ báo cáo

Các mục dưới đây là nhận định tại thời điểm rà soát. Một phần đã được triển khai và chạy lại sau đó; trạng thái và kết quả mới nằm ở mục **Cập nhật triển khai** cuối tài liệu. Các đề xuất chưa có dữ liệu đủ tin cậy vẫn cần xử lý riêng.

| Ưu tiên | Nhiệm vụ | Quan sát có bằng chứng | Cải tiến đề xuất và phạm vi chạy lại |
|---|---|---|---|
| Cao | NV1 | `is_valid_session` hiện chỉ loại lỗi `charging > total` và vượt ngưỡng công suất. Trong 259.356 phiên được đánh dấu hợp lệ có **12 phiên `end_datetime_utc <= start_datetime_utc`** và **481 phiên lệch thời lượng ghi so với chênh lệch timestamp >59 giây**; NV4 loại 481 phiên này. | Giữ cờ NV1 hiện tại để truy vết nhưng thêm cờ riêng `valid_connection_interval` và `timestamp_consistent_59s`, rồi công bố một bảng flow số phiên cho từng phân tích. Không đổi nghĩa `is_valid_session` một cách âm thầm vì sẽ làm thay đổi toàn bộ kết quả downstream. Nếu quyết định đổi tập chuẩn thì chạy lại NV1–NV5. |
| Cao | NV2 | Notebook tự lọc CSV với ngưỡng công suất 19,2 kW và kiểm tra timestamp, trong khi NV1 dùng Level 2 = 22 kW. Notebook NV2 còn câu nhận xét `13/18` DBSCAN, nhưng bảng output của chính notebook có **11/18** cấu hình một cụm. CSV NV2 ở `outputs/tables/` là lượt chạy 259.356 phiên, khác notebook 258.720. | Chốt bộ lọc NV2 và giải thích rõ 19,2 kW nếu giữ; sửa câu DBSCAN; xuất bảng/hình từ **một pipeline NV2 duy nhất** kèm số phiên, seed và phiên bản dữ liệu. Nếu chuyển sang `sessions_features.parquet` NV1, chạy lại toàn bộ phân cụm và không giữ số liệu/hình cũ. |
| Cao | NV3 | `3.3.3_stats.csv` có Energy Delta −0,0281, CI bootstrap [−0,061; 0,002] chứa 0, nhưng p-value MWU và Holm rất nhỏ. Code ghi rõ Holm chỉ sửa p-value MWU tham khảo, không xử lý phụ thuộc cùng User ID. | Trong kết luận chính, dùng Delta + CI bootstrap theo user; đánh dấu Energy là chưa vững theo CI. Muốn một p-value chính thức, xây dựng phép kiểm định/CI ở cấp user hoặc bootstrap phù hợp và chạy lại NV3. Đừng dùng cột “Có ý nghĩa (Holm)” làm kết luận duy nhất. |
| Trung bình | NV1 | `port_id` trong parquet có **139 cách viết**, chuẩn hóa MAC/cổng còn **117 ID**. Hàm kiểm tra overlap hiện nhóm theo ID chưa chuẩn hóa; trên dữ liệu hiện tại số overlap vẫn là **181** ở cả hai cách. `convert_to_utc` mặc định múi giờ lạ/thiếu thành UTC; dữ liệu hiện tại không có giá trị múi giờ lạ. | Chuẩn hóa ID cổng một lần ở NV1 và dùng cho mọi nhiệm vụ; thêm cờ timezone không nhận diện được thay vì mặc định UTC. Đây là cải tiến độ bền, chưa làm đổi số overlap hiện tại nhưng tránh sai ở dữ liệu mới. |
| Trung bình | NV3 | Phân khúc `Regular` dùng `Pre_Session_Count >= 10`; người dùng chỉ xuất hiện sau chính sách luôn nhận 0 và bị xếp `Casual` nếu có postal code. Bảng thành phần Pre/Post vì thế chịu ảnh hưởng của cách định nghĩa theo giai đoạn trước. Bunching hiện chỉ là tỷ số hai ô 5 phút quanh mốc 20. | Nêu rõ `Regular` là **người dùng thường xuyên ở giai đoạn Pre**, tách người dùng mới Post thành nhóm riêng, hoặc định nghĩa phân khúc theo quy tắc áp dụng được cho cả hai kỳ rồi chạy lại NV3. Với bunching, kiểm tra độ nhạy độ rộng bin và báo khoảng bất định trước khi dùng ngôn ngữ “tích tụ bất thường”. |
| Trung bình | NV4 | C1 số phiên và C2 tổng kWh có tương quan Pearson **0,982**; hai tiêu chí cùng chiếm khoảng **57,2%** trọng số Entropy. Bỏ C1 trong S2 làm 7/33 trạm đổi ít nhất 5 bậc, top 5 còn trùng 3/5. Ma trận dùng tổng số phiên/tổng kWh của toàn giai đoạn, nên trạm hoạt động lâu hơn có lợi thế quy mô. | Giữ bảng TOPSIS hiện hành làm phân tích chính, nhưng thêm kịch bản **phiên/ngày hoạt động** và **kWh/cổng/ngày hoạt động** nếu có lịch sử cổng đáng tin cậy. Báo rõ thiếu dữ liệu công suất/lịch hoạt động nếu không thể tính. Đưa S1/S2/S6 vào thảo luận độ nhạy, tránh gọi thứ hạng là tuyệt đối. |
| Thấp | NV1–NV4 | `tests/` hiện có kiểm tra NV1, NV4/TOPSIS, NV5 nhưng chưa có kiểm tra riêng cho flow NV2 và kết luận NV3. Kết quả output trong Git đã được ignore, nên người khác clone repo không có sẵn các CSV để đối chiếu. | Thêm kiểm tra có ý nghĩa cho số phiên qua từng bộ lọc, tổng kích thước cụm, DBSCAN 11/18, CI/nhãn kết luận NV3; lưu metadata gồm phiên bản dữ liệu, tham số, seed và checksum để mọi bảng/hình truy được về lượt chạy. |

**Thứ tự triển khai gợi ý:** (1) khóa định nghĩa mẫu NV1/NV2/NV4; (2) sửa mâu thuẫn và bảng/hình cũ; (3) củng cố suy luận NV3; (4) thử độ nhạy chuẩn hóa quy mô NV4. Không đổi đồng thời bộ lọc và thuật toán mà vẫn so trực tiếp các chỉ số trước/sau, vì khi đó nguồn chênh lệch không xác định được.

## Cập nhật triển khai ngày 11/11/2026

| NV | Đã cải tiến và chạy lại | Kết quả kiểm tra | Còn cần làm khi sửa báo cáo |
|---|---|---|---|
| NV1 | Giữ định nghĩa `is_valid_session`; thêm cờ múi giờ lạ, khoảng kết nối UTC không dương và lệch timestamp quá 59 giây vào parquet/audit. Múi giờ lạ không còn bị ngầm coi là UTC. | 259.415 dòng gốc, 259.356 phiên `is_valid_session`; 0 múi giờ lạ, 12 khoảng không dương và 521 lệch timestamp trên tập sau bỏ trùng. Trong tập NV1-valid có 481 phiên lệch timestamp. | Tách rõ tập NV1-valid khỏi tập NV2/NV4; các cờ mới chưa phải điều kiện loại của NV1. |
| NV2 | Sửa đường dẫn dữ liệu theo repo, cập nhật diễn giải k=4 và DBSCAN 11/18, xuất `outputs/nv2/` từ chính notebook kèm số phiên, seed và tham số lọc. | Chạy hết notebook; 258.720 phiên phân tích, k=4, 11/18 cấu hình DBSCAN thành một cụm. | Bảng/hình trong PDF phải lấy từ lượt notebook này; nêu rõ ngưỡng 19,2 kW là bộ lọc riêng NV2. |
| NV3 | Tách `New_Post` khỏi `Casual`; thêm nhãn kết luận theo CI bootstrap theo User ID. | Chạy hết notebook; `New_Post` chiếm 55,98% phiên Post. Energy Delta −0,0281, CI [−0,061; 0,002] nên nhãn `Chưa rõ`. | Không diễn giải thay đổi Pre/Post là tác động nhân quả; p-value MWU/Holm chỉ tham khảo do phụ thuộc theo user. |
| NV4 | Xuất `outputs/nv4_rank_robustness.json` từ notebook và script, gồm tương quan tiêu chí và biến động hạng S1/S2/S6. | Chạy lại bộ tạo bảng/hình: 33 trạm; C1/C2 tương quan 0,982, tổng trọng số 57,2%; S2 làm 7 trạm đổi ít nhất 5 bậc và top 5 trùng 3/5. | Thảo luận độ nhạy xếp hạng; chưa có lịch sử số cổng/ngày hoạt động đáng tin cậy để chuẩn hóa theo mức phơi nhiễm. |

Các file trong `outputs/` bị Git ignore, nên thành viên khác cần chạy lại notebook/script để tạo số liệu. Tập kiểm tra mã NV1/NV4 hiện có chạy thành công (15 bài kiểm tra). `IS403.pdf` và bản PDF ghi khác biệt được giữ nguyên làm tài liệu đối chiếu; cần cập nhật bản thảo báo cáo từ bảng mới trước khi nộp.
