"""
Module: evaluation.py
Mô tả: Bộ chỉ số đánh giá chất lượng dữ liệu, hiệu suất vận hành trạm sạc, đánh giá phân cụm và mô hình dự báo.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def compute_quality_metrics(df: pd.DataFrame, initial_count: int, dup_count: int) -> Dict[str, Any]:
    """
    Tính toán các chỉ số kiểm soát chất lượng dữ liệu (NV1).
    """
    total_valid = int(df['is_valid_session'].sum())
    curr_len = len(df)
    
    return {
        'initial_rows': initial_count,
        'deduplicated_rows': curr_len,
        'exact_duplicates_removed': dup_count,
        'charging_gt_total_count': int(df['flag_charging_gt_total'].sum()),
        'physical_power_anomalies_count': int(df['flag_physical_power_anomaly'].sum()),
        'zero_energy_sessions_count': int(df['flag_zero_energy'].sum()),
        'port_overlaps_count': int(df['flag_port_overlap'].sum()),
        'outlier_duration_count': int(df['flag_outlier_duration_iqr'].sum()),
        'outlier_charging_count': int(df['flag_outlier_charging_iqr'].sum()),
        'outlier_energy_count': int(df['flag_outlier_energy_iqr'].sum()),
        'valid_clean_sessions': total_valid,
        'valid_rate_percentage': round(total_valid / curr_len * 100, 3)
    }


def compute_occupancy_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """
    Tính toán các chỉ số hành vi chiếm dụng trạm sạc (NV2 & NV3).
    """
    valid = df[df['is_valid_session']].copy()
    
    idle_hours = valid['idle_time_hours']
    idle_ratios = valid['idle_ratio']
    
    total_idle_hours = float(idle_hours.sum())
    total_connected_hours = float(valid['total_duration_hours'].sum())
    
    macro_idle_share = (total_idle_hours / total_connected_hours * 100) if total_connected_hours > 0 else 0.0
    
    return {
        'mean_idle_time_hours': float(idle_hours.mean()),
        'median_idle_time_hours': float(idle_hours.median()),
        'mean_idle_ratio': float(idle_ratios.mean()),
        'median_idle_ratio': float(idle_ratios.median()),
        'macro_idle_share_percentage': float(macro_idle_share),
        'severe_idle_session_pct': float((idle_ratios > 0.5).mean() * 100)
    }


def compute_station_benchmarks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán chỉ số KPI cấp trạm sạc (NV4).
    """
    valid = df[df['is_valid_session']].copy()
    
    agg_funcs = {
        'total_duration_hours': ['count', 'sum', 'mean'],
        'charging_time_hours': 'sum',
        'idle_time_hours': ['sum', 'mean'],
        'idle_ratio': 'mean',
        'Energy (kWh)': ['sum', 'mean']
    }
    
    station_stats = valid.groupby('Station Name').agg(agg_funcs)
    station_stats.columns = [
        'total_sessions', 'total_connect_hours', 'avg_connect_hours',
        'total_charging_hours', 'total_idle_hours', 'avg_idle_hours',
        'avg_idle_ratio', 'total_energy_kwh', 'avg_energy_kwh'
    ]
    
    # Tính tỷ lệ thời gian sạc thực tế trên tổng thời gian kết nối
    station_stats['utilization_efficiency'] = (
        station_stats['total_charging_hours'] / station_stats['total_connect_hours']
    ).round(4)
    
    return station_stats.sort_values(by='total_sessions', ascending=False)


def evaluate_forecast_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Đánh giá độ chính xác mô hình dự báo nhu cầu phụ tải (NV5): MAE, RMSE, MAPE.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    
    nonzero_mask = y_true != 0
    if np.any(nonzero_mask):
        mape = float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100)
    else:
        mape = np.nan
        
    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape
    }

