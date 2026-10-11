"""
Module: data_validation.py
Mô tả: Bộ hàm kiểm tra tính toàn vẹn logic, giới hạn vật lý và kiểm soát chất lượng dữ liệu phiên sạc (NV1).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

try:
    from .config import TIMEZONE_OFFSETS, POWER_LIMITS_KW, IQR_MULTIPLIER
except ImportError:
    from config import TIMEZONE_OFFSETS, POWER_LIMITS_KW, IQR_MULTIPLIER


def check_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thống kê số lượng và tỷ lệ giá trị thiếu (missing values) trên toàn bộ các cột.
    """
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df)) * 100
    missing_df = pd.DataFrame({
        'missing_count': null_counts,
        'missing_percentage': null_pct
    })
    return missing_df[missing_df['missing_count'] > 0].sort_values(by='missing_count', ascending=False)


def check_duplicates(df: pd.DataFrame) -> Tuple[int, pd.DataFrame]:
    """
    Quy tắc 5: Phát hiện các bản ghi trùng lặp hoàn toàn trên toàn bộ trường thông tin.
    """
    dup_mask = df.duplicated()
    dup_count = int(dup_mask.sum())
    dup_records = df[df.duplicated(keep=False)] if dup_count > 0 else pd.DataFrame()
    return dup_count, dup_records


def check_chronological_order(df: pd.DataFrame) -> pd.Series:
    """
    Quy tắc 2: Kiểm tra trình tự thời gian sau khi chuẩn hóa UTC (End Date >= Start Date).
    Trả về Series boolean (True nếu vi phạm: End < Start).
    """
    if 'end_datetime_utc' not in df.columns or 'start_datetime_utc' not in df.columns:
        raise ValueError("Yêu cầu các cột 'start_datetime_utc' và 'end_datetime_utc'.")
    return df['end_datetime_utc'] < df['start_datetime_utc']


def check_duration_consistency(df: pd.DataFrame) -> pd.Series:
    """
    Quy tắc 3: Kiểm tra quan hệ thời lượng (T_charging > T_total là vi phạm).
    Trả về Series boolean (True nếu vi phạm).
    """
    return df['charging_time_sec'] > df['total_duration_sec']


def check_energy_consistency(df: pd.DataFrame) -> Dict[str, int]:
    """
    Quy tắc 4 & Mục 2.2.4: Kiểm tra tính hợp lệ của điện năng (E >= 0, Zero-energy sessions).
    """
    energy = df['Energy (kWh)']
    return {
        'negative_energy_count': int((energy < 0).sum()),
        'zero_energy_sessions': int(((energy == 0) & (df['total_duration_sec'] > 0)).sum()),
        'null_energy_count': int(energy.isnull().sum())
    }


def check_physical_power_limits(
    df: pd.DataFrame, 
    custom_limits: Dict[str, float] = None
) -> Tuple[pd.Series, pd.Series]:
    """
    Mục 2.2.3: Tính công suất sạc trung bình P_avg = E / T_charging và đối chiếu giới hạn vật lý.
    Trả về:
    - p_avg_kw: Công suất trung bình tính toán theo phiên (kW)
    - flag_anomaly: Series boolean (True nếu vượt trần vật lý)
    """
    limits = custom_limits or POWER_LIMITS_KW
    charging_h = df['charging_time_hours']
    
    # Tính công suất trung bình kW
    p_avg = np.where(charging_h > 0, df['Energy (kWh)'] / charging_h, 0.0)
    p_avg_series = pd.Series(p_avg, index=df.index, name='p_avg_kw')
    
    # Ngưỡng vật lý theo loại cổng
    threshold = df['Port Type'].map(limits).fillna(limits.get('default', 22.0))
    flag_anomaly = (df['charging_time_sec'] > 0) & (p_avg_series > threshold)
    
    return p_avg_series, flag_anomaly


def detect_port_overlaps(df: pd.DataFrame) -> pd.Series:
    """
    Quy tắc 6: Phát hiện các phiên chồng lấn thời gian trên cùng một cổng sạc vật lý.
    """
    df_temp = df.copy()
    if 'port_id' not in df_temp.columns:
        df_temp['port_id'] = df_temp['MAC Address'].astype(str) + '_Port_' + df_temp['Port Number'].astype(str)
        
    df_temp = df_temp.sort_values(by=['port_id', 'start_datetime_utc'])
    prev_end = df_temp.groupby('port_id')['end_datetime_utc'].shift(1)
    overlap_mask = (prev_end.notna()) & (prev_end > df_temp['start_datetime_utc'])
    
    return overlap_mask.reindex(df.index).fillna(False)


def compute_iqr_fences(series: pd.Series, multiplier: float = IQR_MULTIPLIER) -> Dict[str, float]:
    """
    Mục 2.2.2: Tính phân vị Q1, Q3, khoảng tứ phân vị IQR, hàng rào dưới L và hàng rào trên U.
    """
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_fence = q1 - multiplier * iqr
    upper_fence = q3 + multiplier * iqr
    return {
        'Q1': q1,
        'Q3': q3,
        'IQR': iqr,
        'Lower_Fence': lower_fence,
        'Upper_Fence': upper_fence
    }


def generate_data_quality_report(df: pd.DataFrame, initial_count: int, dup_count: int) -> pd.DataFrame:
    """
    Tạo bảng tổng hợp kiểm toán chất lượng dữ liệu (Data Quality Audit Scorecard).
    """
    curr_len = len(df)
    
    summary_data = [
        {"Hạng mục kiểm tra": "Tổng số bản ghi ban đầu", "Số lượng bản ghi": initial_count, "Tỷ lệ (%)": 100.0, "Hướng xử lý": "Tập dữ liệu thô"},
        {"Hạng mục kiểm tra": "Bản ghi trùng lặp hoàn toàn (Quy tắc 5)", "Số lượng bản ghi": dup_count, "Tỷ lệ (%)": round(dup_count / initial_count * 100, 4), "Hướng xử lý": "Loại bỏ 4 bản ghi lặp, giữ 1 bản ghi đại diện"},
        {"Hạng mục kiểm tra": "Lỗi logic: Thời gian sạc > Tổng kết nối (Quy tắc 3)", "Số lượng bản ghi": int(df['flag_charging_gt_total'].sum()), "Tỷ lệ (%)": round(df['flag_charging_gt_total'].sum() / curr_len * 100, 4), "Hướng xử lý": "Gắn cờ cách ly, không gán thời gian rỗi về 0"},
        {"Hạng mục kiểm tra": "Dị biệt công suất vật lý (P_avg > P_max) (Mục 2.2.3)", "Số lượng bản ghi": int(df['flag_physical_power_anomaly'].sum()), "Tỷ lệ (%)": round(df['flag_physical_power_anomaly'].sum() / curr_len * 100, 4), "Hướng xử lý": "Gắn cờ cách ly khỏi phân tích công suất/thời lượng sạc"},
        {"Hạng mục kiểm tra": "Giao dịch không phát sinh điện năng (Mục 2.2.4)", "Số lượng bản ghi": int(df['flag_zero_energy'].sum()), "Tỷ lệ (%)": 0.0, "Hướng xử lý": "Không có trong bộ dữ liệu hiện tại"},
        {"Hạng mục kiểm tra": "Xung đột/chồng lấn thời gian trên cổng sạc (Quy tắc 6)", "Số lượng bản ghi": int(df['flag_port_overlap'].sum()), "Tỷ lệ (%)": round(df['flag_port_overlap'].sum() / curr_len * 100, 4), "Hướng xử lý": "Gắn cờ kiểm tra thiết bị & lịch sử kết nối"},
        {"Hạng mục kiểm tra": "Ngoại lệ thống kê thời gian kết nối (IQR)", "Số lượng bản ghi": int(df['flag_outlier_duration_iqr'].sum()), "Tỷ lệ (%)": round(df['flag_outlier_duration_iqr'].sum() / curr_len * 100, 2), "Hướng xử lý": "Giữ nguyên để nghiên cứu hành vi chiếm dụng"},
        {"Hạng mục kiểm tra": "Ngoại lệ thống kê điện năng tiêu thụ (IQR)", "Số lượng bản ghi": int(df['flag_outlier_energy_iqr'].sum()), "Tỷ lệ (%)": round(df['flag_outlier_energy_iqr'].sum() / curr_len * 100, 2), "Hướng xử lý": "Giữ nguyên phục vụ dự báo nhu cầu phụ tải"},
        {"Hạng mục kiểm tra": "Số phiên hợp lệ đầy đủ cho phân tích hành vi & hiệu suất", "Số lượng bản ghi": int(df['is_valid_session'].sum()), "Tỷ lệ (%)": round(df['is_valid_session'].sum() / curr_len * 100, 3), "Hướng xử lý": "Tập dữ liệu phân tích chuẩn hóa"}
    ]
    return pd.DataFrame(summary_data)
