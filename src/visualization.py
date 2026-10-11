"""
Module: visualization.py
Mô tả: Thư viện các hàm trực quan hóa dữ liệu chuẩn mực phục vụ báo cáo và phân tích đồ án.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import Union


def set_plotting_style():
    """
    Cấu hình phong cách biểu đồ thống nhất cho toàn bộ dự án.
    """
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.size': 11,
        'figure.autolayout': True,
        'axes.titlesize': 13,
        'axes.labelsize': 11,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 14
    })


def plot_distributions(
    df: pd.DataFrame, 
    output_path: Union[str, Path] = None,
    show: bool = False
) -> plt.Figure:
    """
    Vẽ 3 biểu đồ Histogram & KDE phân phối: T_total, T_charging, Energy.
    """
    set_plotting_style()
    val = df[~df['flag_charging_gt_total']]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 1. Total Duration
    sns.histplot(val['total_duration_hours'], bins=50, kde=True, ax=axes[0], color='#1f77b4')
    axes[0].set_title('Phân phối Tổng thời gian kết nối (T_total)')
    axes[0].set_xlabel('Thời gian (giờ)')
    axes[0].set_ylabel('Số lượng phiên')
    axes[0].set_xlim(0, 24)
    axes[0].axvline(5.969, color='red', linestyle='--', label='Hàng rào trên IQR (5.969h)')
    axes[0].legend()
    
    # 2. Charging Time
    sns.histplot(val['charging_time_hours'], bins=50, kde=True, ax=axes[1], color='#2ca02c')
    axes[1].set_title('Phân phối Thời gian sạc thực tế (T_charging)')
    axes[1].set_xlabel('Thời gian (giờ)')
    axes[1].set_ylabel('Số lượng phiên')
    axes[1].set_xlim(0, 15)
    axes[1].axvline(5.183, color='red', linestyle='--', label='Hàng rào trên IQR (5.183h)')
    axes[1].legend()
    
    # 3. Energy
    sns.histplot(val['Energy (kWh)'], bins=50, kde=True, ax=axes[2], color='#ff7f0e')
    axes[2].set_title('Phân phối Điện năng tiêu thụ (Energy)')
    axes[2].set_xlabel('Điện năng (kWh)')
    axes[2].set_ylabel('Số lượng phiên')
    axes[2].set_xlim(0, 60)
    axes[2].axvline(22.970, color='red', linestyle='--', label='Hàng rào trên IQR (22.970 kWh)')
    axes[2].legend()
    
    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300)
    if show:
        plt.show()
    return fig


def plot_boxplots(
    df: pd.DataFrame, 
    output_path: Union[str, Path] = None,
    show: bool = False
) -> plt.Figure:
    """
    Vẽ 3 biểu đồ hộp (Boxplots) thể hiện độ lệch phải và các ngoại lệ thống kê.
    """
    set_plotting_style()
    val = df[~df['flag_charging_gt_total']]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    sns.boxplot(y=val['total_duration_hours'], ax=axes[0], color='#aec7e8')
    axes[0].set_title('Biểu đồ hộp Tổng thời gian kết nối')
    axes[0].set_ylabel('Thời gian (giờ)')
    axes[0].axhline(5.969, color='red', linestyle='--', label='U = 5.969h')
    axes[0].legend()
    
    sns.boxplot(y=val['charging_time_hours'], ax=axes[1], color='#98df8a')
    axes[1].set_title('Biểu đồ hộp Thời gian sạc')
    axes[1].set_ylabel('Thời gian (giờ)')
    axes[1].axhline(5.183, color='red', linestyle='--', label='U = 5.183h')
    axes[1].legend()
    
    sns.boxplot(y=val['Energy (kWh)'], ax=axes[2], color='#ffbb78')
    axes[2].set_title('Biểu đồ hộp Điện năng tiêu thụ')
    axes[2].set_ylabel('Điện năng (kWh)')
    axes[2].axhline(22.970, color='red', linestyle='--', label='U = 22.970 kWh')
    axes[2].legend()
    
    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300)
    if show:
        plt.show()
    return fig


def plot_power_anomalies(
    df: pd.DataFrame, 
    output_path: Union[str, Path] = None,
    show: bool = False
) -> plt.Figure:
    """
    Vẽ phân phối công suất sạc trung bình và đánh dấu ngưỡng trần vật lý.
    """
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    
    valid_p = df[(df['charging_time_hours'] > 0) & (df['p_avg_kw'] <= 30)]['p_avg_kw']
    sns.histplot(valid_p, bins=60, kde=True, ax=ax, color='#9467bd')
    ax.set_title('Phân phối Công suất sạc trung bình (P_avg = E / T_charging) và Ngưỡng vật lý')
    ax.set_xlabel('Công suất trung bình (kW)')
    ax.set_ylabel('Số lượng phiên sạc')
    ax.axvline(7.2, color='orange', linestyle='--', label='Định mức chuẩn Level 2 CT4000 (7.2 kW)')
    ax.axvline(22.0, color='red', linestyle='-', linewidth=2, label='Ngưỡng trần vật lý AC Level 2 (22.0 kW)')
    
    ax.annotate(
        'Bản ghi dị biệt TED THOMPSON #1:\nP_avg = 419.4 kW (Vượt ngoài biểu đồ)', 
        xy=(22, 10000), 
        xytext=(15, 30000),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5)
    )
    ax.legend()
    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300)
    if show:
        plt.show()
    return fig

