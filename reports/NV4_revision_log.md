# NHẬT KÝ KIỂM TOÁN VÀ CẢI TIẾN NHIỆM VỤ 4 (NV4 REVISION & AUDIT LOG)
**Đề tài:** Đánh giá và so sánh hiệu suất mạng lưới trạm sạc xe điện (Palo Alto, California)  
**Môn học:** IS403 — Phân tích Dữ liệu Kinh doanh (Business Analyst)  
**Ngày hoàn thành:** 04/11/2026  
**Người thực hiện:** Senior Data Analyst & Scientific Python Engineer  

---

## 1. TỔNG QUAN HIỆN TRẠNG TRƯỚC KHI CẢI TIẾN (BASELINE AUDIT)

Trước khi thực hiện cải tiến, Nhiệm vụ 4 (NV4) bao gồm:
1. Notebook `notebooks/04_NV4_station_benchmarking.ipynb` ở trạng thái thử nghiệm sơ khởi:
   - Dừng lại ở khâu trích xuất đặc trưng C1–C6, chuẩn hóa Min-Max và tính toán hai bộ trọng số Entropy vs. Equal Weights.
   - Chưa triển khai thuật toán TOPSIS (thiếu ma trận quyết định có trọng số, điểm lý tưởng $A^+, A^-$, khoảng cách Euclidean $D^+, D^-$, và hệ số tiệm cận tương đối $CC_i$).
   - Thiếu bảng xếp hạng đầy đủ (Table A) và bảng Top/Bottom (Table B).
   - Thiếu trực quan hóa kết quả xếp hạng (Hình A: Barh TOPSIS score, Hình B: Slope chart so sánh thứ hạng Entropy vs. Equal, Hình C: Biểu đồ phân tán chỉ số và xếp hạng).
   - Thiếu phân tích mức độ đồng thuận thứ hạng cơ sở (Baseline agreement) và phân tích độ nhạy (Sensitivity analysis: Scenarios S0–S6).
   - Chưa có unit test để kiểm thử thuật toán xếp hạng độc lập.
2. Báo cáo phương pháp luận (Mục 3.4):
   - Đã có Mục 3.4.1 (Xây dựng ma trận tiêu chí) và Mục 3.4.2 (Chuẩn hóa Min-Max và xác định trọng số), nhưng còn một số điểm chưa chuẩn xác về phương pháp luận (ví dụ: tuyên bố các tiêu chí không được phụ thuộc tất định vào nhau trong khi $C2 = C1 \times C3$; diễn giải chiều hướng của $C4$; tính chất trung bình phiên của $C5$).
   - Hoàn toàn khuyết thiếu Mục 3.4.3 (Quy trình xếp hạng đa tiêu chí TOPSIS, kết quả thực nghiệm và kiểm tra độ nhạy).

---

## 2. CÁC VẤN ĐỀ ĐÃ PHÁT HIỆN VÀ PHƯƠNG ÁN XỬ LÝ

| STT | Thành phần | Vấn đề phát hiện | Nguyên nhân / Đánh giá | Phương án xử lý |
|:---:|:---|:---|:---|:---|
| 1 | **Dữ liệu đầu vào & Quy mô mẫu** | Các con số thống kê (258.720 phiên hợp lệ, 46 trạm, 33 trạm đủ điều kiện $\ge 500$ phiên, 258.681 phiên phân tích) cần được kiểm chứng độc lập từ pipeline dữ liệu thô thay vì chấp nhận thụ động. | Nguy cơ sai lệch dây chuyền từ NV1 hoặc các bước lọc trước đó. | Viết script kiểm tra độc lập `scripts/verify_raw_pipeline.py` đối chiếu tuần tự qua 5 bước lọc NV1: 259.415 $\to$ bỏ trùng (259.411) $\to$ logic thời gian (259.366) $\to$ trần công suất 19,2 kW (259.356) $\to$ dung sai sai lệch thời gian $\le 59$ giây (258.720). Xác nhận chính xác 46 trạm ban đầu, 33 trạm $\ge 500$ phiên (chứa đúng 258.681 phiên, chiếm 99,985%). |
| 2 | **Mối quan hệ phụ thuộc $C2 = C1 \times C3$** | Báo cáo cũ khẳng định "các tiêu chí không được là hàm số tất định của nhau", nhưng trên thực tế $C2$ (Tổng sản lượng kWh) chính bằng $C1$ (Số phiên) nhân $C3$ (Sản lượng bình quân kWh/phiên). | Hiểu nhầm lý thuyết MCDM: việc kết hợp tiêu chí quy mô tích lũy và tiêu chí hiệu suất bình quân là phổ biến, nhưng đòi hỏi phải giải trình thấu đáo về mức độ tương quan cao ($r = 0,919$). | Sửa lại báo cáo Mục 3.4.1: thừa nhận công khai quan hệ $C2 = C1 \times C3$, giải thích góc nhìn hệ thống (C1 phản ánh thông lượng giao dịch, C2 phản ánh tải lưới tích lũy, C3 phản ánh cường độ sạc mỗi lượt), đồng thời đưa kịch bản loại bỏ $C2$ (S1) và $C1$ (S2) vào phân tích độ nhạy. |
| 3 | **Chiều hướng tiêu chí $C4$ (Công suất trung bình)** | Tiêu chí $C4$ (Mean Charging Power, kW) được định nghĩa là Benefit (+), nhưng trạm có công suất cao có thể do xe nhận công suất lớn hoặc thiết bị hỗ trợ tốt hơn, không hoàn toàn do vận hành trạm. | Trạm Level 2 phụ thuộc vào bộ sạc trên xe (OBC). Nếu coi $C4$ là Benefit thì ưu tiên trạm sạc nhanh, nhưng liệu có làm lệch xếp hạng không? | Giữ nguyên $C4$ là Benefit theo thiết kế gốc để đảm bảo tính nhất quán kế thừa, nhưng bổ sung Kịch bản S4 (loại bỏ $C4$) vào phân tích độ nhạy để đo lường tác động ($\rho = 0,9926$ chứng minh thứ hạng cực kỳ ổn định). |
| 4 | **Đặc tính đo lường của $C5$ (Tỷ lệ chiếm dụng vô ích)** | $C5$ được tính bằng trung bình cộng tỷ lệ nhàn rỗi theo phiên ($\frac{1}{N}\sum \frac{T_{idle}}{T_{total}}$), thay vì tổng thời gian nhàn rỗi chia tổng thời gian cắm sạc ($\frac{\sum T_{idle}}{\sum T_{total}}$). | Phép tính này gán trọng số đồng đều cho mỗi phiên sạc bất kể thời lượng, dễ bị kéo lệch bởi các phiên sạc rất ngắn hoặc rất dài. | Giải trình rõ đặc tính "phiên bình quân" (session-weighted) trong báo cáo, đồng thời thiết kế Kịch bản S5 (tính $C5$ theo thời lượng thực tế) trong phân tích độ nhạy. Kết quả $\rho = 0,9977$ chứng minh chỉ số phiên là đại diện xuất sắc cho thực tế vận hành. |
| 5 | **Sự dư thừa giữa $C5$ và $C6$** | Hệ số tương quan Pearson giữa $C5$ và $C6$ đạt $r = 0,9852$ (Spearman $\rho = 0,9766$). | Cả hai đều là tiêu chí Cost phản ánh tổn thất thời gian nhàn rỗi ($C5$ tính theo tỷ lệ %, $C6$ tính theo số giờ tuyệt đối), tạo ra trọng số kép (double-counting) cho hành vi nhàn rỗi. | Thừa nhận hiện tượng tương quan cao trong phân tích tương quan và thiết kế Kịch bản S3 (loại bỏ $C6$). Kết quả độ nhạy cho thấy thứ hạng gần như không đổi ($\rho = 0,9967$, độ lệch bình quân 0,36 bậc). |
| 6 | **Khuyết thiếu thuật toán TOPSIS** | Notebook chưa có mã nguồn cài đặt TOPSIS, thiếu toàn bộ các bước tính toán theo chuẩn MCDM. | Hạn chế tiến độ ban đầu của notebook. | Cài đặt hoàn chỉnh thuật toán Min-Max TOPSIS 5 bước bằng Python chuẩn hóa vector hóa (NumPy, Pandas), đảm bảo tính toán chính xác, tái lập 100%, không sử dụng thư viện MCDM ngoại vi hộp đen. |
| 7 | **Thiếu kiểm thử phần mềm độc lập** | Chưa có test tự động kiểm tra tính đúng đắn của logic TOPSIS (trường hợp biên, thống trị tuyệt đối, đồng nhất giá trị). | Nguy cơ lỗi tính toán ẩn trong hàm TOPSIS. | Xây dựng tệp kiểm thử `tests/test_topsis.py` với 3 kịch bản: (1) Trạm thống trị tuyệt đối phải đạt điểm cao nhất ($CC=1,0$); (2) Các phương án đồng nhất phải nhận điểm bằng nhau; (3) Kiểm thử trên ma trận 1 tiêu chí. Đạt 100% test passed (`pytest`). |
| 8 | **Thiếu hệ thống phân tích độ nhạy** | Chưa đánh giá độ bền vững của thứ hạng khi thay đổi giả định trọng số hoặc tập tiêu chí. | Xếp hạng MCDM thường bị phê bình là nhạy cảm với phương pháp trọng số hoặc lựa chọn tiêu chí. | Xây dựng bộ khung phân tích độ nhạy toàn diện gồm 7 kịch bản (S0 đến S6), so sánh ma trận tương quan Spearman/Kendall, độ dịch chuyển thứ hạng cực đại và trung bình. |

---

## 3. CÁC QUYẾT ĐỊNH PHƯƠNG PHÁP LUẬN VÀ CƠ SỞ KHOA HỌC

1. **Chuẩn hóa Min-Max kết hợp TOPSIS (Min-Max TOPSIS):**
   - *Cơ sở:* Ma trận quyết định ban đầu đã được chuẩn hóa tuyến tính Min-Max theo đúng chiều hướng Benefit (+) và Cost (-), đưa toàn bộ các chỉ số về thang đo không thứ nguyên $[0, 1]$, trong đó $1$ luôn đại diện cho trạng thái tối ưu và $0$ là trạng thái kém nhất.
   - *Hệ quả:* Nghiệm lý tưởng dương trở thành $v_j^+ = w_j$ và nghiệm lý tưởng âm là $v_j^- = 0$. Khoảng cách Euclidean được tính nhất quán trên không gian đã định hướng, giúp việc diễn giải hình học trở nên trực quan, minh bạch. Kịch bản S6 (TOPSIS vector cổ điển của Hwang & Yoon, 1981) được bổ sung để so sánh đối chứng ($\rho = 0,8877$).
2. **So sánh Trọng số Entropy khách quan vs. Trọng số Equal chủ quan:**
   - *Trọng số Entropy ($w_{entropy}$):* C1 (0,2939) > C2 (0,2772) > C3 (0,2078) > C4 (0,0997) > C5 (0,0656) > C6 (0,0557). Phản ánh mức độ phân tán thông tin thực nghiệm cao ở các tiêu chí quy mô tích lũy ($C1, C2$).
   - *Trọng số Equal ($w_{equal}$):* Gán giá trị đồng đều $\frac{1}{6} \approx 0,1667$ cho cả 6 tiêu chí, phản ánh quan điểm quản trị cân bằng giữa thông lượng, năng lượng và chất lượng phục vụ.
   - *Độ đồng thuận (Baseline Agreement):* Hệ số tương quan hạng Spearman $\rho = 0,8185$, Kendall $\tau = 0,6288$. Độ lệch thứ hạng trung bình là 4,30 bậc; độ lệch lớn nhất là 14 bậc (`TED THOMPSON #4` tăng từ hạng 26 lên 12 do có hiệu suất thời gian $C5, C6$ xuất sắc). Top 5 có 3 trạm xuất hiện đồng thời (`HAMILTON #2`, `WEBSTER #1`, `WEBSTER #2`).
3. **Phân tích Độ nhạy Đa kịch bản (Sensitivity Framework S0–S6):**
   - *S0 (Baseline Entropy):* Mô hình cơ sở đầy đủ 6 tiêu chí.
   - *S1 (Bỏ C2):* $\rho = 0,9545$, loại trừ sự thống trị quy mô điện năng.
   - *S2 (Bỏ C1):* $\rho = 0,9228$, loại trừ sự thống trị thông lượng phiên.
   - *S3 (Bỏ C6):* $\rho = 0,9967$, triệt tiêu sự dư thừa do tương quan đa cộng tuyến với C5.
   - *S4 (Bỏ C4):* $\rho = 0,9926$, đánh giá mức độ phụ thuộc vào công suất sạc bình quân.
   - *S5 (C5 gia quyền thời lượng):* $\rho = 0,9977$, kiểm tra giả định trung bình phiên vs. trung bình giờ.
   - *S6 (Vector-normalized TOPSIS):* $\rho = 0,8877$, kiểm tra tính nhạy cảm với kỹ thuật chuẩn hóa.

---

## 4. TỔNG HỢP DANH MỤC TỆP ĐÃ TẠO VÀ CHỈNH SỬA

### 4.1. Mã nguồn & Notebooks
- `notebooks/04_NV4_station_benchmarking.ipynb`: Tái cấu trúc hoàn chỉnh 11 cell mã nguồn kèm markdown học thuật chi tiết, thực thi thành công 100% không lỗi (execution_count từ 1 đến 11). Nhúng toàn bộ biểu đồ và bảng kết quả trực tiếp vào notebook.
- `tests/test_topsis.py`: Tệp kiểm thử đơn vị với 3 test cases cho hàm tính toán TOPSIS, đảm bảo độ tin cậy phần mềm.
- `scripts/build_nv4_notebook.py`: Script tự động tạo notebook NV4 chuẩn hóa, đồng bộ nội dung markdown và code cells.
- `scripts/generate_all_nv4_assets.py`: Script tính toán toàn bộ pipeline dữ liệu, xuất bảng số liệu CSV và biểu đồ PNG độ phân giải cao (300 DPI).
- `scripts/verify_raw_pipeline.py`: Script kiểm chứng số liệu đầu vào từ tệp dữ liệu thô.

### 4.2. Dữ liệu đầu ra (Outputs)
- `outputs/nv4_station_criteria.csv`: Ma trận tiêu chí gốc C1–C6 của 33 trạm sạc đủ điều kiện.
- `outputs/nv4_criteria_weights.csv`: Bảng tổng hợp độ phân tán Entropy ($e_j, d_j$) và so sánh trọng số Entropy vs. Equal.
- `outputs/nv4_topsis_rankings.csv`: Bảng kết quả xếp hạng TOPSIS chi tiết ($D^+, D^-, CC$, Thứ hạng) cho cả hai phương pháp trọng số và các kịch bản độ nhạy.
- `outputs/nv4_sensitivity_analysis.csv`: Bảng tổng hợp chỉ số tương quan Spearman, Kendall, độ lệch thứ hạng cực đại và trung bình qua các kịch bản S0–S6.

### 4.3. Biểu đồ chất lượng cao (Figures - 300 DPI)
- `outputs/figures/hinh_3_4_tuong_quan_tieu_chi.png` & `reports/figures/hinh_3_4_tuong_quan_tieu_chi.png`: Ma trận tương quan Pearson và Spearman giữa 6 tiêu chí C1–C6.
- `outputs/figures/hinh_3_5_ma_tran_chuan_hoa.png` & `reports/figures/hinh_3_5_ma_tran_chuan_hoa.png`: Heatmap giá trị chuẩn hóa Min-Max của 33 trạm sạc.
- `outputs/figures/hinh_3_6_trong_so.png` & `reports/figures/hinh_3_6_trong_so.png`: Biểu đồ cột so sánh trọng số Entropy và Equal Weights.
- `outputs/figures/hinh_3_7_diem_topsis.png` & `reports/figures/hinh_3_7_diem_topsis.png`: Biểu đồ thanh ngang (Hình A) xếp hạng điểm tiệm cận TOPSIS $CC_i$.
- `outputs/figures/hinh_3_8_so_sanh_thu_hang.png` & `reports/figures/hinh_3_8_so_sanh_thu_hang.png`: Biểu đồ Slope Chart (Hình B) so sánh dịch chuyển thứ hạng giữa Entropy và Equal Weights.
- `outputs/figures/hinh_3_9_phan_tan_diem.png` & `reports/figures/hinh_3_9_phan_tan_diem.png`: Biểu đồ phân tán (Hình C) giữa điểm TOPSIS và thứ hạng, phân nhóm 4 cụm tứ phân vị.
- `outputs/figures/hinh_3_10_phan_tich_do_nhay.png` & `reports/figures/hinh_3_10_phan_tich_do_nhay.png`: Biểu đồ phân tích độ nhạy trực quan hóa chỉ số Spearman và độ lệch thứ hạng qua các kịch bản S0–S6.

### 4.4. Tài liệu báo cáo (Reports)
- `reports/NV4_section_3_4_3.md`: Bản thảo học thuật hoàn chỉnh của Mục 3.4.3 (Quy trình xếp hạng đa tiêu chí TOPSIS) bằng tiếng Việt theo đúng cấu trúc tiêu chuẩn (a đến h).
- `reports/3.4_phuong_phap_danh_gia_hieu_suat_tram_sac.md`: Báo cáo tích hợp toàn diện bao gồm toàn bộ Chương 3.4 (từ 3.4, 3.4.1, 3.4.2 đến 3.4.3), đồng bộ hóa toàn bộ công thức toán học, bảng biểu và diễn giải phân tích.
- `reports/NV4_revision_log.md`: Nhật ký kiểm toán, cải tiến và giải trình phương pháp luận (chính tệp tài liệu này).

---

## 5. CÁC HẠN CHẾ PHÂN TÍCH VÀ ĐỀ XUẤT CHO NGHIÊN CỨU TIẾP THEO

1. **Hiệu ứng phụ thuộc thời gian (Time-aggregated bias):**
   - Phân tích hiện tại tổng hợp toàn bộ dữ liệu giao dịch trong nhiều năm thành một giá trị trung bình đại diện duy nhất cho mỗi trạm. Cách tiếp cận này bỏ qua sự biến động theo mùa, xu hướng tăng trưởng của xe điện qua các năm, cũng như sự khác biệt giữa ngày trong tuần và cuối tuần.
   - *Hướng cải tiến:* Trong các nghiên cứu tương lai hoặc phần mở rộng Dashboard, có thể áp dụng TOPSIS động theo chuỗi thời gian (Dynamic TOPSIS / Window-based Benchmarking).
2. **Quy mô cổng sạc vật lý (Physical Port Capacity):**
   - Bộ dữ liệu công khai của Palo Alto định danh trạm theo tên địa điểm (Station Name) mà không cung cấp chính xác số lượng cổng sạc vật lý (ports/plugs) đồng thời tại mỗi thời điểm trong quá khứ. Do đó, tiêu chí quy mô $C1$ phản ánh tổng số lượt phục vụ tuyệt đối của cụm địa điểm thay vì hiệu suất trên từng đầu cắm sạc đơn lẻ.
3. **Mối quan hệ nhân quả vs. Đo lường mô tả:**
   - TOPSIS là kỹ thuật xếp hạng vận trù học mô tả, không mô hình hóa cơ chế nhân quả kinh tế lượng (chẳng hạn như vị trí gần trung tâm thương mại hay mức giá sạc ảnh hưởng thế nào đến thời gian cắm sạc nhàn rỗi).
   - Việc kết hợp kết quả phân cụm hành vi từ NV2 hoặc phân tích chính sách giá từ NV3 sẽ giúp hoàn thiện bức tranh quản trị toàn diện hơn.

