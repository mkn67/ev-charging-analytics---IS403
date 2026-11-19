# Vị trí cần cập nhật trong báo cáo NV5

Các số dưới đây lấy từ `outputs/nv5/method_audit_20261119/` và hai kỳ kiểm chứng trong thư mục con `robustness/`. Bảng và ảnh đã dựng lại nằm trong thư mục con [bao_cao_4_5](../outputs/nv5/method_audit_20261119/bao_cao_4_5/).

## Mục 3.5 — Phương pháp

| Vị trí trong bản thảo | Thay hoặc bổ sung |
|---|---|
| Câu mở đầu “XGBoost được đối chiếu với sáu mô hình cơ sở” | Thêm “trong thí nghiệm chính”. Baseline luôn 0 chỉ thuộc phân tích bổ sung cho số phiên bắt đầu. |
| 3.5.1, sau đoạn “Bộ đặc trưng gồm…” | Thêm “Đặc trưng lịch được tính theo giờ địa phương Palo Alto (America/Los_Angeles), có tính giờ mùa hè. Lưới 15 phút và ranh giới các tập sử dụng UTC.” |
| 3.5.2, đoạn “Persistent Baseline – Lag-1 Day…” | Đổi thành “Ba đối chứng persistence lấy giá trị quan sát ở khung liền trước (t−1), 96 khung trước (t−96) hoặc 672 khung trước (t−672) trên lưới UTC.” Hai độ trễ dài là 24 và 168 giờ theo lưới, giờ địa phương có thể lệch khi đổi giờ mùa hè. |
| 3.5.2, sau đoạn Random Forest | Chèn đoạn về baseline 0 bên dưới. |
| 3.5.3 | Giữ hai cấu hình XGBoost và cách chọn bằng validation. |
| 3.5.4, sau Bảng 3.17 và phần mô tả stress | Giữ Bảng 3.17 cho thí nghiệm chính. Thêm đoạn kiểm chứng theo thời gian bên dưới. |

Đoạn chèn ở **3.5.2**:

> Phân tích bổ sung cho số phiên bắt đầu sử dụng đối chứng luôn dự báo 0. Các dự báo được chấm trên cùng những khung kiểm thử ở tám cụm có chuỗi mục tiêu biến động. Sai số được tổng hợp trên toàn kỳ và riêng cho ba nhóm khung có 0, 1 hoặc từ 2 phiên quan sát được. MAE, RMSE và sai lệch có dấu được tính theo từng cụm rồi lấy trung bình đều. Các nhóm được xác định sau khi có quan sát để chẩn đoán sai số.

Đoạn chèn ở **3.5.4**:

> Ngoài phép chia chính, nghiên cứu kiểm tra độ ổn định của dự báo chiếm dụng qua hai cửa sổ lịch sử. Với kỳ kiểm thử nửa cuối năm 2018, mô hình được huấn luyện trên dữ liệu đến hết năm 2017 và chọn cấu hình trên nửa đầu năm 2018. Với kỳ kiểm thử nửa đầu năm 2019, mô hình được huấn luyện trên dữ liệu đến hết nửa đầu năm 2018 và chọn cấu hình trên nửa cuối năm 2018. Mỗi cửa sổ huấn luyện lại hai cấu hình XGBoost theo cụm, chọn bằng RMSE validation và chấm cùng các khung với đối chứng t−1 theo giao thức dự báo một bước. Các mốc chia dùng UTC. Hai cửa sổ phục vụ kiểm chứng hồi cứu, trong đó kỳ nửa đầu năm 2019 trùng với validation của thí nghiệm chính.

## Mục 4.5 — Bảng và câu diễn giải

| Vị trí | Thay bằng kết quả nào |
|---|---|
| Mở đầu 4.5, nếu còn câu “cả tám cụm” và “bảy trong tám cụm” | Trong test chính, XGBoost có RMSE thấp nhất trong bảy mô hình ở **7/8 cụm occupancy** và **6/8 cụm arrivals**. Phân biệt kết quả so với từng baseline và vị trí dẫn đầu trong tất cả mô hình. |
| **4.5.1a / Bảng 4.5.1** | Giữ số khung và đoạn cấu hình được chọn. Hai kỳ lịch sử được báo cáo ở bảng bổ sung. |
| **4.5.1b / Bảng 4.5.2** | Dùng CSV Bảng 4.5.2. Trung bình 9 cụm: XGBoost occupancy đạt MAE **0,2705**, RMSE **0,4652**, R² **0,9131**. t−1 có MAE **0,2148** và RMSE **0,4883**. XGBoost giảm RMSE **4,72%** so với t−1. Arrivals có RMSE tốt nhất ở Random Forest (**0,3621**), gần với XGBoost (**0,3623**). Historical Mean có MAE tốt nhất trong bảy mô hình chính (**0,1936**). |
| **4.5.1b / Đoạn SHERMAN** | Sau khi bỏ SHERMAN, XGBoost đạt MAE/RMSE/R² **0,3043 / 0,5234 / 0,9022** với occupancy và **0,2395 / 0,4076 / 0,1189** với arrivals. |
| **4.5.1c / Bảng 4.5.3 và 4.5.4** | Dùng hai CSV theo cụm. XGBoost occupancy giảm RMSE **2,86–6,33%** so với t−1 ở cả 8 cụm, nhưng Random Forest có RMSE thấp hơn tại **RINCONADA LIB**. Với arrivals, XGBoost giảm RMSE **0,50–10,78%** so với Historical Mean, và Random Forest có RMSE thấp hơn tại **CAMBRIDGE, WEBSTER**. R² arrivals của XGBoost trên tám cụm khoảng **0,0486–0,1719**. |
| **4.5.1d / Bảng 4.5.5** | Dùng CSV stress 2020. Occupancy: t−1 có MAE thấp nhất (**0,0996**). XGBoost có RMSE **0,322145**, so với **0,322563** của t−1. Hai số rất sát nhau. Arrivals: Ridge có RMSE thấp nhất (**0,2419**), t−672 có MAE thấp nhất (**0,1004**), R² của XGBoost là **0,0503**. |
| **4.5.1e / Bảng 4.5.6** | Dùng CSV occupancy theo trạng thái. Giữ **111.764/141.312 khung giữ nguyên (79,09%)**. Khi occupancy thay đổi, MAE t−1 → XGBoost là **1,1375 → 1,0139**, RMSE là **1,2007 → 1,0946**. Khi giữ nguyên, MAE/RMSE của XGBoost là **0,1156 / 0,1735**, t−1 có sai số bằng 0. |
| **4.5.1e / Bảng 4.5.7** | Thay bằng bảng arrivals dưới đây, có thêm hai cột Always zero và Random Forest. Nếu giữ cột sai lệch XGBoost, giá trị theo nhóm 0/1/≥2 lần lượt là **+0,1344 / −0,7223 / −1,7955**. |
| **4.5.2 / Bảng 4.5.8 và các đoạn b, c** | Dùng CSV gain theo nhóm và CSV gain theo từng đặc trưng. Occupancy có lag ngắn hạn **78,96%**, riêng lag 1 **66,28%**, rolling **19,22%**. Arrivals có lịch **43,60%**, rolling **42,58%**, lag ngày/tuần **11,60%**, lag ngắn **2,22%**. Đặc trưng đứng đầu arrivals là rolling 12 khung (**29,79%**), kế tiếp là hour_cos (**15,31%**). |
| **4.5.3c / Bảng 4.5.9** | Dùng CSV chiếm dụng cao và chọn đúng các hàng đã có trong bản thảo. Giữ số **40.218/141.312 khung (28,46%)** và ngưỡng theo cụm. Ở nhóm này, XGBoost có MAE/RMSE/sai lệch **0,5153 / 0,7072 / −0,2728**, còn t−1 có **0,4123 / 0,7276 / −0,1283**. |
| **4.5.3, ngay sau Bảng 4.5.9** | Thêm mục **d) Kiểm chứng theo thời gian**, đặt **Bảng 4.5.10** như bên dưới. Đổi tiểu mục tổng hợp hiện tại từ **d)** thành **e)**. |

**Bảng 4.5.7. MAE arrivals theo số phiên thực tế trong kỳ test nửa cuối 2019**

| Số phiên thực tế | Số khung | Luôn 0 | Historical Mean | Random Forest | XGBoost |
|---|---:|---:|---:|---:|---:|
| 0 | 120.877 | 0,0000 | 0,0812 | 0,1446 | 0,1344 |
| 1 | 17.178 | 1,0000 | 0,8511 | 0,7016 | 0,7227 |
| ≥2 | 3.257 | 2,1217 | 1,9574 | 1,7646 | 1,7955 |
| Toàn kỳ | 141.312 | 0,1716 | 0,2178 | 0,2438 | 0,2395 |

> Có 85,54% số khung không phát sinh phiên, giúp đối chứng luôn 0 đạt MAE thấp nhất trên toàn kỳ. Ở các khung có từ hai phiên trở lên, Random Forest và XGBoost giảm MAE so với đối chứng này nhưng vẫn dự báo thấp. RMSE toàn kỳ của đối chứng luôn 0 là 0,4698, so với 0,4073 của Random Forest và 0,4076 của XGBoost. Các giá trị trong bảng là trung bình đều trên tám cụm có hoạt động.

**Bảng 4.5.10. Sai số dự báo occupancy theo các kỳ kiểm thử**

| Kỳ kiểm thử | MAE t−1 | MAE XGBoost | RMSE t−1 | RMSE XGBoost | Thay đổi RMSE của XGBoost |
|---|---:|---:|---:|---:|---:|
| Nửa cuối 2018 | 0,2238 | 0,3604 | 0,5236 | 0,6816 | Tăng 30,16% |
| Nửa đầu 2019 | 0,2413 | 0,2985 | 0,5458 | 0,5179 | Giảm 5,11% |
| Nửa cuối 2019, kỳ chính | 0,2416 | 0,3043 | 0,5493 | 0,5234 | Giảm 4,72% |

> Các chỉ số là trung bình đều trên tám cụm có chuỗi chiếm dụng biến động ở mỗi kỳ. XGBoost có RMSE thấp hơn t−1 trong hai kỳ năm 2019. Trong nửa cuối năm 2018, XGBoost giảm RMSE tại sáu cụm nhưng tăng mạnh ở CAMBRIDGE và TED THOMPSON, làm RMSE trung bình tăng 30,16%. Persistence t−1 có MAE trung bình thấp hơn trong cả ba kỳ. Mức cải thiện theo RMSE khác nhau giữa các giai đoạn và các cụm.

Ở đoạn tổng hợp cuối 4.5.3, dùng kết luận trên cho occupancy. Với arrivals, ghi Random Forest và XGBoost có RMSE tương đương trong kỳ chính, trong khi các đợt đến nhiều phiên còn bị dự báo thấp. Phạm vi ứng dụng là một khung 15 phút kế tiếp khi có quan sát kịp thời từ khung trước.

## Hình cần chèn

| Hình | Vị trí | Hành động |
|---|---|---|
| **4.5.1** | 4.5.2, sau Bảng 4.5.8 | Thay bằng [Gain theo nhóm](../outputs/nv5/method_audit_20261119/bao_cao_4_5/Hình%204.5.1%20-%20Gain%20theo%20nhóm.png). |
| **4.5.2** | 4.5.3a, tuần test 12–18/08/2019 | Thay bằng [BRYANT 2019](../outputs/nv5/method_audit_20261119/bao_cao_4_5/Hình%204.5.2%20-%20BRYANT%202019.png). |
| **4.5.3** | 4.5.3a, tuần stress 10–16/08/2020 | Thay bằng [BRYANT 2020](../outputs/nv5/method_audit_20261119/bao_cao_4_5/Hình%204.5.3%20-%20BRYANT%202020.png). |
| **4.5.4** | 4.5.3b, chiếm dụng theo giờ BRYANT | Có thể giữ. Đã đối chiếu lại số quan sát và các mức nêu trong đoạn văn vẫn khớp. Có [bản dựng lại](../outputs/nv5/method_audit_20261119/bao_cao_4_5/Hình%204.5.4%20-%20BRYANT%20theo%20giờ.png) để đồng bộ kiểu hình nếu cần. |

Hai kiểm chứng mới được trình bày đủ bằng Bảng 4.5.7 và 4.5.10.

## Chương 5 — Chỉnh đúng các đoạn NV5

- **5.1.2, đoạn có dẫn 4.5.3:** giữ nội dung về giờ cao tại BRYANT. Số quan sát theo giờ vẫn khớp với Hình 4.5.4.
- **5.1.3, đoạn bắt đầu “NV5 có thể hỗ trợ…”:** giữ **79,09%**, đổi sai lệch ở các khung chiếm dụng cao từ **−0,2707** thành **−0,2728 cổng**. Giữ khuyến nghị xác nhận tình trạng cổng trước khi chốt lịch bảo trì.
- **5.2, thay riêng đoạn bắt đầu “NV5 đưa 259.344 phiên…”** bằng đoạn sau:

> NV5 sử dụng 259.344 phiên để xây dựng chuỗi 15 phút. Trong kỳ kiểm thử nửa cuối năm 2019, XGBoost dự báo số cổng có phiên kết nối với RMSE 0,4652 cổng và R² 0,9131 khi lấy trung bình trên chín cụm. So với đối chứng t−1, XGBoost giảm RMSE 4,72% trong kỳ này và 5,11% trong nửa đầu năm 2019, nhưng RMSE tăng 30,16% trong nửa cuối năm 2018. Đối chứng t−1 có MAE trung bình thấp hơn ở cả ba kỳ. Với số phiên bắt đầu, Random Forest và XGBoost có RMSE lần lượt là 0,3621 và 0,3623 phiên mỗi khung trong kỳ chính. Dự báo luôn 0 có MAE thấp nhất trong phân tích bổ sung, trong khi cả hai mô hình cây giảm sai số ở các khung có phiên nhưng vẫn đánh giá thấp các đợt đến cao.

- **5.3, đoạn bắt đầu “NV5 được đánh giá…”:** đổi R² arrivals **0,2165 → 0,2168** trên 9 cụm và **0,1186 → 0,1189** trên 8 cụm có hoạt động. Sau câu về stress 2020, thêm “Kết quả ở hai kỳ lịch sử cho thấy mức cải thiện RMSE của XGBoost phụ thuộc vào giai đoạn và địa điểm.” Giữ phần hướng phát triển dự báo nhiều bước và dữ liệu công suất.

Nếu **4.1.2** liệt kê bốn tập của thiết kế chính, có thể thêm một câu dẫn “Hai kỳ kiểm chứng bổ sung cho occupancy được trình bày tại Bảng 4.5.10.”
