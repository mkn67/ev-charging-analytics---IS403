"""
Module: feature_engineering.py
Mô tả: Tiền xử lý, chuyển đổi thời gian, trích xuất đặc trưng T_idle, Idle Ratio và các biến phục vụ phân cụm, dự báo.
"""

import pandas as pd
import numpy as np
from typing import Tuple
try:
    from .config import TIMEZONE_OFFSETS
    from .data_validation import (
        check_duplicates,
        check_duration_consistency,
        check_physical_power_limits,
        detect_port_overlaps,
        compute_iqr_fences
    )
except ImportError:
    from config import TIMEZONE_OFFSETS
    from data_validation import (
        check_duplicates,
        check_duration_consistency,
        check_physical_power_limits,
        detect_port_overlaps,
        compute_iqr_fences
    )


def parse_duration_to_seconds(series: pd.Series) -> pd.Series:
    """
    Quy đổi chuỗi thời lượng 'hh:mm:ss' sang giây.
    """
    parts = series.astype(str).str.split(':', expand=True).astype(float)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def parse_dates_robust(series: pd.Series) -> pd.Series:
    """
    Chuyển đổi chuỗi ngày tháng sang datetime64, phục hồi cả số serial Excel (vd: '42845.81041').
    """
    is_numeric = series.str.match(r'^\d+(\.\d+)?$').fillna(False)
    res = pd.Series(index=series.index, dtype='datetime64[ns]')
    
    if is_numeric.any():
        res[is_numeric] = pd.to_datetime(
            series[is_numeric].astype(float), 
            unit='D', 
            origin='1899-12-30'
        )
    if (~is_numeric).any():
        res[~is_numeric] = pd.to_datetime(
            series[~is_numeric], 
            format='%m/%d/%Y %H:%M'
        )
    return res


def convert_to_utc(dt_series: pd.Series, tz_series: pd.Series) -> pd.Series:
    """
    Chuẩn hóa dấu thời gian sang UTC dựa vào múi giờ (PDT, PST, UTC).
    """
    deltas = pd.to_timedelta(tz_series.map(TIMEZONE_OFFSETS).fillna(0), unit='h')
    return dt_series - deltas


def compute_idle_metrics(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Tính toán thời gian nhàn rỗi (Idle Time) và Idle Ratio.
    T_idle = T_total - T_charging
    Idle_Ratio = T_idle / T_total
    Chỉ tính cho các phiên hợp lệ (T_total >= T_charging), các phiên lỗi logic để NaN.
    """
    valid_mask = ~df['flag_charging_gt_total']
    
    idle_sec = np.where(valid_mask, df['total_duration_sec'] - df['charging_time_sec'], np.nan)
    idle_hours = idle_sec / 3600.0
    
    total_pos = df['total_duration_sec'] > 0
    idle_ratio = np.where(valid_mask & total_pos, idle_sec / df['total_duration_sec'], np.nan)
    
    return (
        pd.Series(idle_sec, index=df.index, name='idle_time_sec'),
        pd.Series(idle_hours, index=df.index, name='idle_time_hours'),
        pd.Series(idle_ratio, index=df.index, name='idle_ratio')
    )


def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trích xuất các đặc trưng thời gian và phân loại phiên sạc (phục vụ NV2, NV4, NV5).
    """
    out = df.copy()
    dt = out['start_datetime_utc']
    
    out['start_hour'] = dt.dt.hour
    out['start_dayofweek'] = dt.dt.dayofweek  # 0=Monday, 6=Sunday
    out['start_day_name'] = dt.dt.day_name()
    out['is_weekend'] = out['start_dayofweek'].isin([5, 6]).astype(int)
    out['start_month'] = dt.dt.month
    out['start_year'] = dt.dt.year
    out['start_date'] = dt.dt.date
    
    # Phân loại phiên sạc: Ban ngày (Daytime: 6h-18h), Buổi tối (Evening: 18h-22h), Qua đêm (Overnight: 22h-6h)
    hour = out['start_hour']
    conditions = [
        (hour >= 6) & (hour < 18),
        (hour >= 18) & (hour < 22),
        (hour >= 22) | (hour < 6)
    ]
    choices = ['Daytime', 'Evening', 'Overnight']
    out['time_of_day_category'] = np.select(conditions, choices, default='Daytime')
    
    # Phân loại mức độ chiếm dụng (Occupancy severity) dựa trên Idle Ratio
    idle_r = out['idle_ratio']
    occ_conditions = [
        idle_r.isna(),
        idle_r == 0,
        (idle_r > 0) & (idle_r <= 0.2),
        (idle_r > 0.2) & (idle_r <= 0.5),
        idle_r > 0.5
    ]
    occ_choices = ['Invalid', 'No_Idle', 'Low_Idle', 'Medium_Idle', 'Severe_Idle']
    out['idle_severity_level'] = np.select(occ_conditions, occ_choices, default='No_Idle')
    
    return out


def build_clean_pipeline(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Quy trình làm sạch dữ liệu hoàn chỉnh NV1:
    - Loại bỏ duplicate hoàn toàn
    - Chuẩn hóa thời gian & múi giờ
    - Tính toán thời lượng
    - Gắn cờ toàn vẹn logic & giới hạn vật lý
    - Gắn cờ ngoại lệ IQR
    """
    initial_count = len(raw_df)
    
    # 1. Loại bỏ trùng lặp hoàn toàn
    dup_count, _ = check_duplicates(raw_df)
    df = raw_df.drop_duplicates().copy().reset_index(drop=True)
    
    # 2. Quy đổi thời lượng
    df['total_duration_sec'] = parse_duration_to_seconds(df['Total Duration (hh:mm:ss)'])
    df['charging_time_sec'] = parse_duration_to_seconds(df['Charging Time (hh:mm:ss)'])
    df['total_duration_hours'] = df['total_duration_sec'] / 3600.0
    df['charging_time_hours'] = df['charging_time_sec'] / 3600.0
    
    # 3. Chuẩn hóa datetime & múi giờ
    df['start_dt_local'] = parse_dates_robust(df['Start Date'])
    df['end_dt_local'] = parse_dates_robust(df['End Date'])
    df['start_datetime_utc'] = convert_to_utc(df['start_dt_local'], df['Start Time Zone'])
    df['end_datetime_utc'] = convert_to_utc(df['end_dt_local'], df['End Time Zone'])
    
    # 4. Định danh cổng sạc
    df['port_id'] = df['MAC Address'].astype(str) + '_Port_' + df['Port Number'].astype(str)
    
    # 5. Gắn cờ lỗi logic quan hệ thời lượng (T_charging > T_total)
    df['flag_charging_gt_total'] = check_duration_consistency(df)
    
    # 6. Gắn cờ Zero-Energy
    df['flag_zero_energy'] = (df['Energy (kWh)'] == 0) & (df['total_duration_sec'] > 0)
    
    # 7. Tính Idle Time & Idle Ratio
    idle_sec, idle_hours, idle_ratio = compute_idle_metrics(df)
    df['idle_time_sec'] = idle_sec
    df['idle_time_hours'] = idle_hours
    df['idle_ratio'] = idle_ratio
    
    # 8. Gắn cờ công suất sạc vật lý dị biệt
    p_avg, flag_p_anom = check_physical_power_limits(df)
    df['p_avg_kw'] = p_avg
    df['flag_physical_power_anomaly'] = flag_p_anom
    
    # 9. Gắn cờ chồng lấn cổng sạc
    df['flag_port_overlap'] = detect_port_overlaps(df)
    
    # 10. Gắn cờ ngoại lệ thống kê IQR trên tập hợp lệ logic
    val_mask = ~df['flag_charging_gt_total']
    for col, flag_col in [('total_duration_hours', 'flag_outlier_duration_iqr'),
                          ('charging_time_hours', 'flag_outlier_charging_iqr'),
                          ('Energy (kWh)', 'flag_outlier_energy_iqr')]:
        fences = compute_iqr_fences(df.loc[val_mask, col])
        df[flag_col] = df[col] > fences['Upper_Fence']
        
    # 11. Phiên hợp lệ tổng quát
    df['is_valid_session'] = (~df['flag_charging_gt_total']) & (~df['flag_physical_power_anomaly'])
    
    return df, initial_count, dup_count
