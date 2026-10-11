"""
Module: config.py
Mô tả: Quản lý đường dẫn tập trung và các tham số nghiệp vụ cho dự án ev-charging-analytics.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# ĐƯỜNG DẪN DỰ ÁN (PROJECT PATHS)
# ---------------------------------------------------------------------------
# Xác định thư mục gốc dự án (thư mục chứa src/)
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

# Thư mục dữ liệu
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Thư mục outputs
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
FIGURES_DIR = OUTPUTS_DIR / "figures"
MODELS_DIR = OUTPUTS_DIR / "models"
METRICS_DIR = OUTPUTS_DIR / "metrics"

# Thư mục reports
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_FIGURES_DIR = REPORTS_DIR / "figures"

# Thư mục notebooks & tests
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
TESTS_DIR = PROJECT_ROOT / "tests"

# Tập tin dữ liệu chuẩn hóa
RAW_DATA_FILE = RAW_DATA_DIR / "EVChargingStationUsage.csv"
SESSIONS_CLEAN_PARQUET = PROCESSED_DATA_DIR / "sessions_clean.parquet"
SESSIONS_FEATURES_PARQUET = PROCESSED_DATA_DIR / "sessions_features.parquet"
QUALITY_AUDIT_CSV = TABLES_DIR / "data_quality_audit_summary.csv"

# ---------------------------------------------------------------------------
# THAM SỐ NGHIỆP VỤ & VẬT LÝ (BUSINESS & PHYSICAL CONSTANTS)
# ---------------------------------------------------------------------------
# Bản đồ chênh lệch múi giờ so với UTC (giờ)
TIMEZONE_OFFSETS = {
    'PDT': -7,
    'PST': -8,
    'UTC': 0
}

# Giới hạn trần công suất sạc vật lý theo loại cổng (kW)
# Level 1: sạc chậm 120V x 16A ~ 1.92 kW
# Level 2: sạc AC định mức 7.2 kW (ChargePoint CT4000), ngưỡng an toàn tối đa 22.0 kW (3-phase 32A)
POWER_LIMITS_KW = {
    'Level 1': 1.92,
    'Level 2': 22.0,
    'default': 22.0
}
NOMINAL_POWER_LEVEL2_KW = 7.2

# Hệ số hàng rào ngoại lệ khoảng tứ phân vị (Tukey's IQR Fences)
IQR_MULTIPLIER = 1.5

# Cấu hình danh mục cột dữ liệu
DATETIME_COLS = ['Start Date', 'End Date']
TIMEZONE_COLS = ['Start Time Zone', 'End Time Zone']
DURATION_COLS = ['Total Duration (hh:mm:ss)', 'Charging Time (hh:mm:ss)']
NUMERIC_COLS = ['Energy (kWh)', 'GHG Savings (kg)', 'Gasoline Savings (gallons)', 'Fee']
PORT_IDENTIFIER_COLS = ['MAC Address', 'Port Number']

# Random seed cho tính tái lập mô hình
RANDOM_STATE = 42

