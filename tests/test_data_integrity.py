"""
Module: test_data_integrity.py
Mô tả: Bộ kiểm thử tự động (pytest) kiểm tra tính toàn vẹn logic, giới hạn vật lý và chất lượng dữ liệu sạch.
Chạy kiểm thử: pytest tests/test_data_integrity.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Đường dẫn dữ liệu
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = BASE_DIR / "data" / "raw" / "EVChargingStationUsage.csv"
CLEAN_PARQUET = BASE_DIR / "data" / "processed" / "sessions_clean.parquet"
FEATURES_PARQUET = BASE_DIR / "data" / "processed" / "sessions_features.parquet"


@pytest.fixture(scope="module")
def clean_data():
    """Tải dữ liệu sạch sau bước NV1 để chạy test suite."""
    assert CLEAN_PARQUET.exists(), f"Không tìm thấy file: {CLEAN_PARQUET}"
    df = pd.read_parquet(CLEAN_PARQUET)
    return df


@pytest.fixture(scope="module")
def features_data():
    """Tải dữ liệu đặc trưng để kiểm tra schema."""
    assert FEATURES_PARQUET.exists(), f"Không tìm thấy file: {FEATURES_PARQUET}"
    df = pd.read_parquet(FEATURES_PARQUET)
    return df


def test_raw_dataset_exists():
    """Kiểm tra dataset gốc tồn tại và không bị sửa đổi."""
    assert RAW_FILE.exists(), f"File dataset thô không tồn tại tại {RAW_FILE}"
    assert RAW_FILE.stat().st_size > 80_000_000, "Kích thước file dataset gốc không hợp lệ."


def test_no_exact_duplicates_in_clean(clean_data):
    """Quy tắc 5: Xác nhận không còn bản ghi trùng lặp hoàn toàn trong tập sạch."""
    duplicate_count = clean_data.duplicated().sum()
    assert duplicate_count == 0, f"Vẫn còn {duplicate_count} bản ghi trùng lặp hoàn toàn."


def test_chronological_order(clean_data):
    """Quy tắc 2: Kiểm tra trình tự thời gian sau chuẩn hóa UTC (End >= Start)."""
    invalid_sequence = clean_data['end_datetime_utc'] < clean_data['start_datetime_utc']
    assert invalid_sequence.sum() == 0, "Phát hiện phiên có End Date trước Start Date sau chuẩn hóa UTC."


def test_duration_logic_for_valid_sessions(clean_data):
    """Quy tắc 3: Các phiên hợp lệ bắt buộc phải có thời gian sạc <= tổng thời gian kết nối."""
    valid_sessions = clean_data[clean_data['is_valid_session']]
    invalid_durations = valid_sessions['charging_time_sec'] > valid_sessions['total_duration_sec']
    assert invalid_durations.sum() == 0, "Tồn tại phiên hợp lệ nhưng thời gian sạc > tổng kết nối."


def test_idle_metrics_range(clean_data):
    """Kiểm tra tính hợp lệ của Idle Time (>= 0) và Idle Ratio (0 <= ratio <= 1)."""
    valid_sessions = clean_data[clean_data['is_valid_session']]
    
    # Idle Time phải >= 0
    assert (valid_sessions['idle_time_sec'] < 0).sum() == 0, "Idle Time bị âm trên các phiên hợp lệ."
    
    # Idle Ratio phải nằm trong khoảng [0, 1]
    valid_ratio = valid_sessions['idle_ratio'].dropna()
    assert (valid_ratio < 0).sum() == 0, "Idle Ratio nhỏ hơn 0."
    assert (valid_ratio > 1.0001).sum() == 0, "Idle Ratio vượt quá 1.0."


def test_physical_power_limits_for_valid_sessions(clean_data):
    """Mục 2.2.3: Các phiên hợp lệ không được vượt quá trần công suất vật lý AC (22.0 kW)."""
    valid_sessions = clean_data[clean_data['is_valid_session']]
    exceeded_power = valid_sessions['p_avg_kw'] > 22.0
    assert exceeded_power.sum() == 0, "Tồn tại phiên hợp lệ nhưng công suất sạc vượt quá 22.0 kW."


def test_energy_non_negative(clean_data):
    """Quy tắc 4: Điện năng ghi nhận không được âm (E >= 0)."""
    negative_energy = clean_data['Energy (kWh)'] < 0
    assert negative_energy.sum() == 0, "Phát hiện phiên sạc có điện năng âm."


def test_features_parquet_schema(features_data):
    """Kiểm tra schema và các đặc trưng dẫn xuất trong sessions_features.parquet."""
    expected_cols = [
        'start_hour', 'start_dayofweek', 'is_weekend', 
        'start_month', 'time_of_day_category', 'idle_severity_level'
    ]
    for col in expected_cols:
        assert col in features_data.columns, f"Thiếu cột đặc trưng: {col}"
    
    # Giờ bắt đầu trong khoảng [0, 23]
    assert features_data['start_hour'].between(0, 23).all()
    # Ngày trong tuần trong khoảng [0, 6]
    assert features_data['start_dayofweek'].between(0, 6).all()

