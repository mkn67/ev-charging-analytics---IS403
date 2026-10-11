"""
Script: run_pipeline.py
Mô tả: Thực thi toàn bộ pipeline tiền xử lý NV1, tạo các file:
- data/processed/sessions_clean.parquet
- data/processed/sessions_features.parquet
- outputs/tables/data_quality_audit_summary.csv
- outputs/figures/ & reports/figures/
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import time
import pandas as pd
from pathlib import Path

try:
    from .config import (
        RAW_DATA_FILE,
        SESSIONS_CLEAN_PARQUET,
        SESSIONS_FEATURES_PARQUET,
        QUALITY_AUDIT_CSV,
        TABLES_DIR,
        FIGURES_DIR,
        REPORTS_FIGURES_DIR
    )
    from .feature_engineering import build_clean_pipeline, extract_temporal_features
    from .data_validation import generate_data_quality_report
    from .visualization import plot_distributions, plot_boxplots, plot_power_anomalies
except ImportError:
    from config import (
        RAW_DATA_FILE,
        SESSIONS_CLEAN_PARQUET,
        SESSIONS_FEATURES_PARQUET,
        QUALITY_AUDIT_CSV,
        TABLES_DIR,
        FIGURES_DIR,
        REPORTS_FIGURES_DIR
    )
    from feature_engineering import build_clean_pipeline, extract_temporal_features
    from data_validation import generate_data_quality_report
    from visualization import plot_distributions, plot_boxplots, plot_power_anomalies

def main():
    t0 = time.time()
    print("=" * 70)
    print("BẮT ĐẦU THỰC THI PIPELINE TIỀN XỬ LÝ VÀ TRÍCH XUẤT ĐẶC TRƯNG")
    print("=" * 70)
    
    # Đảm bảo các thư mục đầu ra tồn tại
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"1. Đọc dữ liệu thô từ: {RAW_DATA_FILE}")
    df_raw = pd.read_csv(RAW_DATA_FILE, low_memory=False)
    print(f"   -> Số dòng ban đầu: {len(df_raw):,}, Số cột: {len(df_raw.columns)}")
    
    print("2. Thực thi pipeline làm sạch dữ liệu (Dung - NV1)...")
    df_clean, initial_count, dup_count = build_clean_pipeline(df_raw)
    print(f"   -> Số bản ghi sau loại trùng: {len(df_clean):,}")
    print(f"   -> Số phiên hợp lệ tổng thể: {int(df_clean['is_valid_session'].sum()):,}")
    
    print(f"3. Lưu trữ dữ liệu sạch vào: {SESSIONS_CLEAN_PARQUET}")
    df_clean.to_parquet(SESSIONS_CLEAN_PARQUET, index=False, engine='pyarrow')
    print("   -> Đã lưu sessions_clean.parquet thành công!")
    
    print("4. Trích xuất đặc trưng mở rộng (temporal & occupancy features)...")
    df_features = extract_temporal_features(df_clean)
    print(f"   -> Số cột sau trích xuất đặc trưng: {len(df_features.columns)}")
    
    print(f"5. Lưu trữ dữ liệu đặc trưng vào: {SESSIONS_FEATURES_PARQUET}")
    df_features.to_parquet(SESSIONS_FEATURES_PARQUET, index=False, engine='pyarrow')
    print("   -> Đã lưu sessions_features.parquet thành công!")
    
    print("6. Tạo bảng tổng kết kiểm toán chất lượng dữ liệu (Audit Scorecard)...")
    audit_df = generate_data_quality_report(df_clean, initial_count, dup_count)
    audit_df.to_csv(QUALITY_AUDIT_CSV, index=False)
    # Lưu thêm 1 bản vào outputs/tables
    audit_df.to_csv(TABLES_DIR / "data_quality_audit_summary.csv", index=False)
    print(f"   -> Đã lưu bảng kiểm toán tại: {QUALITY_AUDIT_CSV}")
    
    print("7. Tạo các biểu đồ trực quan hóa...")
    # Lưu vào outputs/figures
    plot_distributions(df_clean, output_path=FIGURES_DIR / "distribution_durations_energy.png")
    plot_boxplots(df_clean, output_path=FIGURES_DIR / "boxplots_durations_energy.png")
    plot_power_anomalies(df_clean, output_path=FIGURES_DIR / "power_distribution_anomalies.png")
    
    # Đồng bộ sang reports/figures
    plot_distributions(df_clean, output_path=REPORTS_FIGURES_DIR / "distribution_durations_energy.png")
    plot_boxplots(df_clean, output_path=REPORTS_FIGURES_DIR / "boxplots_durations_energy.png")
    plot_power_anomalies(df_clean, output_path=REPORTS_FIGURES_DIR / "power_distribution_anomalies.png")
    print("   -> Đã lưu và đồng bộ biểu đồ vào outputs/figures/ và reports/figures/")
    
    print("=" * 70)
    print(f"HOÀN THÀNH TOÀN BỘ PIPELINE TRONG {time.time() - t0:.2f} GIÂY!")
    print("=" * 70)

if __name__ == '__main__':
    main()
