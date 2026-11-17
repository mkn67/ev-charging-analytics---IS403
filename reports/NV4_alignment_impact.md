# Ảnh hưởng của bản sửa ghép định danh TOPSIS NV4

## Kết quả chạy lại

Đã chạy toàn bộ notebook NV4 và script xuất bảng, hình từ CSV gốc. Hai luồng xuất cùng một bảng xếp hạng khi đối chiếu theo tên trạm. Điểm của 33 trạm được kiểm tra thêm bằng phép tính khoảng cách Euclid độc lập. Toàn bộ 32 kiểm thử của repository đã đạt.

## Thay đổi gắn với từng trạm

Cả 33 trạm đổi điểm và hạng Entropy, đồng thời cả 33 trạm đổi điểm và hạng trọng số đều so với CSV cũ. Cột số phiên C1 khớp theo tên trạm ở cả hai bản. Top 5 cũ và mới trùng 0/5, độ điều chỉnh hạng Entropy lớn nhất là 29 bậc.

Các điểm số được trả về đúng định danh trạm sau khi sửa. Ví dụ HAMILTON #2 chuyển từ hạng 10 về hạng 1, còn MPL #6 chuyển từ hạng 1 về hạng 12. Số dương trong cột Rank_Entropy_Change của CSV tác động biểu thị số thứ tự hạng mới lớn hơn.

| Trạm | Hạng Entropy cũ | Hạng Entropy đúng | Điểm Entropy đúng | Hạng đều cũ | Hạng đều đúng |
|---|---:|---:|---:|---:|---:|
| HAMILTON #2 | 10 | 1 | 0.723298 | 13 | 2 |
| WEBSTER #1 | 27 | 2 | 0.647613 | 26 | 1 |
| WEBSTER #2 | 14 | 3 | 0.604583 | 25 | 3 |
| HAMILTON #1 | 7 | 4 | 0.512089 | 16 | 9 |
| HIGH #4 | 23 | 5 | 0.506990 | 15 | 10 |
| WEBSTER #3 | 33 | 6 | 0.492506 | 30 | 6 |
| BRYANT #2 | 15 | 7 | 0.483649 | 7 | 16 |
| HIGH #1 | 30 | 8 | 0.478468 | 29 | 8 |
| TED THOMPSON #1 | 29 | 9 | 0.472860 | 28 | 4 |
| BRYANT #1 | 22 | 10 | 0.471556 | 14 | 13 |
| TED THOMPSON #2 | 26 | 11 | 0.395406 | 12 | 5 |
| MPL #6 | 1 | 12 | 0.390432 | 2 | 21 |
| HIGH #3 | 8 | 13 | 0.383237 | 8 | 19 |
| CAMBRIDGE #1 | 25 | 14 | 0.377577 | 27 | 25 |
| BRYANT #4 | 17 | 15 | 0.366472 | 20 | 7 |
| RINCONADA LIB 1 | 28 | 16 | 0.365730 | 33 | 18 |
| RINCONADA LIB 3 | 31 | 17 | 0.355046 | 32 | 20 |
| RINCONADA LIB 2 | 20 | 18 | 0.350503 | 23 | 17 |
| HIGH #2 | 5 | 19 | 0.349624 | 10 | 22 |
| MPL #4 | 19 | 20 | 0.349079 | 22 | 23 |
| MPL #5 | 13 | 21 | 0.346890 | 19 | 24 |
| BRYANT #6 | 32 | 22 | 0.334004 | 31 | 14 |
| BRYANT #5 | 21 | 23 | 0.324473 | 24 | 15 |
| TED THOMPSON #3 | 11 | 24 | 0.322130 | 5 | 11 |
| CAMBRIDGE #2 | 4 | 25 | 0.316724 | 9 | 27 |
| TED THOMPSON #4 | 24 | 26 | 0.312866 | 11 | 12 |
| BRYANT #3 | 18 | 27 | 0.268082 | 17 | 26 |
| MPL #2 | 2 | 28 | 0.210031 | 1 | 33 |
| CAMBRIDGE #5 | 12 | 29 | 0.196495 | 21 | 28 |
| CAMBRIDGE #3 | 16 | 30 | 0.189231 | 18 | 29 |
| MPL #1 | 6 | 31 | 0.187964 | 6 | 32 |
| MPL #3 | 3 | 32 | 0.179308 | 3 | 31 |
| CAMBRIDGE #4 | 9 | 33 | 0.170144 | 4 | 30 |

## Đối soát các thành phần tính toán

Mẫu NV4 có 258.875 phiên hợp lệ. Bảng xếp hạng gồm 33 trạm với 258.836 phiên. Ma trận sáu tiêu chí, các trọng số Entropy, tương quan tiêu chí và các giá trị trong bảng độ nhạy S0–S6 khớp bản trước sửa. Tập giá trị điểm TOPSIS cũng khớp khi so sánh độc lập với tên trạm. Script xuất đầy đủ bổ sung nhãn cột định danh Tiêu chí cho hai CSV tương quan và hai cột trọng số đối sánh trong CSV trọng số, theo định dạng sẵn có của script.

Spearman giữa hạng Entropy và hạng đều vẫn bằng 0,819184, Kendall bằng 0,636364, lệch hạng trung bình 4,303030 và lớn nhất 14. Việc hoán vị đồng thời hai cột hạng giữ các chỉ số tổng hợp này trong CSV cũ, dù các điểm bị gán sai tên trạm.

## Hình và phần báo cáo chịu ảnh hưởng

Hai hình thay đổi sau khi xuất lại gồm hinh_3_7_diem_topsis.png và hinh_3_8_so_sanh_thu_hang.png. Các bản trong outputs/figures và reports/figures khớp nhau. Các hình tương quan, ma trận chuẩn hóa, trọng số, phân tán điểm và độ nhạy trùng bản trước chạy lại.

Mục 4.4.1 cần sử dụng bảng xếp hạng mới. Mục 4.4.2 và các nhận xét hoặc đề xuất nêu tên trạm cần được đối chiếu với bảng này. Các tài liệu phương pháp cũ trong reports/NV4_section_3_4_3.md và reports/3.4_phuong_phap_danh_gia_hieu_suat_tram_sac.md còn số phiên và điểm của lượt chạy cũ, ví dụ HAMILTON #2 ghi 23.666 phiên trong khi bảng hiện hành có 23.682 phiên. Các đoạn đó cần cập nhật số liệu khi hoàn thiện báo cáo.

NV5 đọc dữ liệu phiên NV1, ánh xạ vị trí và mốc thời gian. Các kết quả NV5 hiện hành được giữ làm đối chứng trong lần sửa này. Hai notebook NV3 và NV5 khớp byte với bản chụp trước sửa.

## Phạm vi sửa mã

Hàm build_station_rankings trong src/nv4_analysis.py căn chỉnh cả hai bảng TOPSIS theo tên trạm, kiểm tra định danh duy nhất, đủ tập trạm và các giá trị cần xuất. Notebook NV4, script dựng notebook và script xuất hình cùng gọi hàm này. Các sửa đổi nguồn trong notebook giới hạn ở cell import và cell ghép bảng xếp hạng, các cell bổ sung trước đó được giữ qua lần chạy lại.

Kiểm thử hồi quy bao gồm ba bảng có thứ tự dòng khác nhau, thiếu hoặc sai định danh, trùng định danh và thiếu điểm. Script dựng notebook cũng được chạy trong thư mục tạm để kiểm tra bản notebook sinh mới dùng cùng hàm ghép.
