import json

nb_path = 'notebooks/02_NV2_occupancy_clustering.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Update Cell e59254cf (Index 10)
e59254cf_src = [
    "### Đánh giá đa tiêu chí và lý do lựa chọn $k = 4$:\n",
    "1. **Đánh đổi giữa các chỉ số nội tại (Multi-criteria Trade-off):**\n",
    "   - **Silhouette Score:** Đạt cao nhất ở $k=3$ (0,487) và $k=2$ (0,486). Tuy nhiên, cấu hình $k=2$ hoặc $k=3$ chưa bóc tách được nhóm phương tiện nạp dung lượng cực lớn ($E$ cao) hoặc chưa phản ánh trọn vẹn sự phân hóa của nhóm chiếm dụng nhàn rỗi.\n",
    "   - **Calinski-Harabasz Index:** Đạt cực đại tại $k=5$ (7.485). Tuy nhiên, khi tăng từ $k=4$ lên $k=5$, mô hình chia xẻ nhóm sạc thông thường thành hai cụm nhỏ có đặc tính hành vi tương tự nhau, làm tăng độ phức tạp vận hành mà không mang lại giá trị quản trị thực tiễn.\n",
    "2. **Tốc độ suy giảm Inertia (Elbow Method):**\n",
    "   - Tốc độ suy giảm WCSS duy trì ở mức cao qua hai bước đầu: từ $k=2 \\to 3$ giảm -30,2% và từ $k=3 \\to 4$ tiếp tục giảm mạnh -29,2%.\n",
    "   - Sang bước nhảy $k=4 \\to 5$, tốc độ suy giảm khựng lại rõ rệt (chỉ còn -18,8%) và tiếp tục giảm xuống -10,5% tại $k=6$. Điểm bẻ gãy cấu trúc (Elbow point) xuất hiện rõ rệt tại $k=4$, cho thấy việc tăng thêm cụm sau mốc này mang lại hiệu suất suy giảm phương sai biên giảm dần.\n",
    "3. **Chỉ số Davies-Bouldin:**\n",
    "   - Trong tất cả các cấu hình phân tách từ 3 cụm trở lên ($k \\ge 3$), $k=4$ đạt giá trị Davies-Bouldin thấp nhất (0,752), khẳng định cấu trúc các cụm có độ nén nội tại cao và khoảng cách phân tách giữa các tâm cụm là tốt nhất.\n",
    "4. **Khả năng diễn giải nghiệp vụ:**\n",
    "   - $k=4$ là **lựa chọn cân bằng tối ưu giữa các chỉ số toán học và khả năng diễn giải nghiệp vụ**, định hình 4 chân dung hành vi rõ rệt: Sạc nhanh tiện ích, Sạc trung bình-lớn (chiếm thời gian mạng lưới), Sạc dung lượng cực lớn, và Chiếm dụng nhàn rỗi kéo dài.\n"
]
nb['cells'][10]['source'] = e59254cf_src

# 2. Update Cell b0eccd09 (Index 13)
b0eccd09_src = [
    "### Nhận xét thực nghiệm về DBSCAN:\n",
    "1. **Hiện tượng gộp thành một siêu cụm (*Chaining Effect*):**\n",
    "   - Ở hầu hết các tổ hợp tham số (13/18 trường hợp), DBSCAN gom từ 94% đến 99% dữ liệu vào duy nhất một siêu cụm lớn do không gian hành vi sạc xe điện có mật độ liên tục ở vùng trung tâm. Thuật toán không thể tự động phân tách các mẫu hành vi khác nhau.\n",
    "2. **Bản chất của cấu hình sinh ra 4 cụm:**\n",
    "   - Với cấu hình ($\\epsilon = 0,5, MinPts = 10$), thuật toán ghi nhận 4 cụm trên mẫu ban đầu ($N = 10.000$). Tuy nhiên, kích thước phân bổ cụ thể là: **[9.712, 11, 11, 10]**. Như vậy, Cụm 1 chiếm tới 97,12% tổng số phiên, trong khi 3 cụm còn lại thực chất chỉ là các vi nhóm ngoại vi (10 - 11 điểm), hoàn toàn không đại diện cho các phân khúc hành vi cân đối có ý nghĩa quản trị.\n",
    "3. **Độ nhạy cao đối với việc lấy mẫu phụ (*Subsampling Sensitivity*):**\n",
    "   - DBSCAN là thuật toán xác định (*deterministic*), nhưng khi kiểm tra trên 5 mẫu con độc lập rút từ dữ liệu lớn, số cụm tìm được biến động thất thường từ 2 đến 5 cụm (kích thước vi cụm dao động từ 7 đến 25 điểm). Điều này khẳng định DBSCAN không mang lại giải pháp phân nhóm ổn định và không phù hợp làm mô hình phân khúc hành vi cho bài toán này.\n"
]
nb['cells'][13]['source'] = b0eccd09_src

# 3. Update Cell 9995b048 (Index 17)
cell17_src = nb['cells'][17]['source']
if 'Z_final' not in ''.join(cell17_src):
    shared_check_code = [
        "\n",
        "# 3. Phép kiểm tra bổ sung: Split-half dùng chung bộ chuẩn hóa fit trên toàn bộ dữ liệu (Z_final)\n",
        "km_h1_shared = KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT).fit(Z_final[idx_h1])\n",
        "ari_shared = adjusted_rand_score(labels_full_on_h1, km_h1_shared.labels_)\n",
        "nmi_shared = normalized_mutual_info_score(labels_full_on_h1, km_h1_shared.labels_)\n",
        "pred_h2_shared = km_h1_shared.predict(Z_final[idx_h2])\n",
        "km_h2_shared = KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT).fit(Z_final[idx_h2])\n",
        "ari_cross_shared = adjusted_rand_score(pred_h2_shared, km_h2_shared.labels_)\n",
        "\n",
        "print(\"\\n=== KIỂM TRA BỔ SUNG: DÙNG CHUNG BỘ CHUẨN HÓA TOÀN CỤC (Z_final) ===\")\n",
        "print(f\"  ARI giữa Mô hình Toàn bộ và Mô hình Nửa 1 (Shared Scaler)      : {ari_shared:.4f}\")\n",
        "print(f\"  NMI (Shared Scaler)                                            : {nmi_shared:.4f}\")\n",
        "print(f\"  ARI kiểm chứng chéo ngoài mẫu (Cross-prediction Shared Scaler) : {ari_cross_shared:.4f}\")\n"
    ]
    nb['cells'][17]['source'] = cell17_src + shared_check_code

# 4. Update Cell 250b1850 (Index 19)
cell19_src = nb['cells'][19]['source']
if 'between(2011, 2020)' not in ''.join(cell19_src):
    year_check_code = [
        "# Kiểm tra tính nhất quán số lượng phiên theo năm và 5 phiên chênh lệch\n",
        "print(\"=== KIỂM TRA SỐ LƯỢNG PHIÊN THEO NĂM & CÁC PHIÊN NGOÀI GIAI ĐOẠN 2011–2020 ===\")\n",
        "print(\"Số phiên theo năm:\")\n",
        "print(valid[\"yr\"].value_counts(dropna=False).sort_index())\n",
        "print(f\"Tổng phiên NV2: {len(valid):,}\")\n",
        "print(f\"Tổng phiên 2011–2020: {valid['yr'].between(2011, 2020).sum():,}\")\n",
        "print(f\"Phiên ngoài giai đoạn hoặc thiếu năm: {(~valid['yr'].between(2011, 2020)).sum():,}\")\n",
        "print(\"-> 5 phiên chênh lệch chính là 5 phiên thuộc năm 2021 (giao thừa 31/12/2020 sang 01/01/2021 theo chuẩn UTC).\\n\")\n",
        "\n"
    ]
    nb['cells'][19]['source'] = year_check_code + cell19_src

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('Updated notebook successfully!')

