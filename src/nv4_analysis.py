"""Shared NV4 session validation and station-criteria construction."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import POWER_LIMITS_KW, IQR_MULTIPLIER
from .feature_engineering import parse_dates_robust, convert_to_utc

TIMESTAMP_TOLERANCE_SECONDS = 59
MIN_STATION_SESSIONS = 500
SEVERE_IDLE_RATIO = 0.5
NV4_CRITERIA = {
    "C1_so_phien": ("Số phiên sạc", "phiên", +1),
    "C2_tong_dien_nang": ("Tổng điện năng", "kWh", +1),
    "C3_dien_nang_moi_phien": ("Điện năng bình quân mỗi phiên", "kWh/phiên", +1),
    "C4_gio_sac_moi_phien": ("Thời gian sạc hữu ích bình quân", "giờ/phiên", +1),
    "C5_ty_le_nhan_roi": ("Tỷ lệ chiếm dụng nhàn rỗi", "tỷ lệ", -1),
    "C6_ty_le_chiem_dung_nghiem_trong": ("Tỷ lệ phiên chiếm dụng nghiêm trọng", "tỷ lệ", -1),
}


def _duration_seconds(values: pd.Series) -> pd.Series:
    parts = values.astype("string").str.split(":", expand=True)
    if parts.shape[1] != 3:
        return pd.Series(np.nan, index=values.index, dtype=float)
    h = pd.to_numeric(parts[0], errors="coerce")
    m = pd.to_numeric(parts[1], errors="coerce")
    s = pd.to_numeric(parts[2], errors="coerce")
    return h * 3600 + m * 60 + s


def prepare_nv4_sessions(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Apply NV1-aligned checks and return clean sessions plus a row audit.

    The timestamp consistency check uses NV1's robust date parser and UTC offsets.
    Power limits come from config.py by Port Type.
    """
    required = {
        "Total Duration (hh:mm:ss)", "Charging Time (hh:mm:ss)", "Energy (kWh)",
        "Port Type", "Station Name", "Start Date", "End Date", "Start Time Zone", "End Time Zone",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Missing NV4 source columns: {missing}")

    raw_rows = len(raw)
    df = raw.drop_duplicates().copy().reset_index(drop=True)
    after_dedup = len(df)
    df["total_s"] = _duration_seconds(df["Total Duration (hh:mm:ss)"])
    df["charging_s"] = _duration_seconds(df["Charging Time (hh:mm:ss)"])
    df["total_h"] = df["total_s"] / 3600.0
    df["charging_h"] = df["charging_s"] / 3600.0
    df["energy_kwh"] = pd.to_numeric(df["Energy (kWh)"], errors="coerce")
    power = df["energy_kwh"].div(df["charging_h"].where(df["charging_h"].gt(0)))
    nv1_power_limits = df["Port Type"].map(POWER_LIMITS_KW).fillna(POWER_LIMITS_KW["default"])
    nv1_valid = (~df["charging_s"].gt(df["total_s"])) & ~(
        df["charging_s"].gt(0) & power.gt(nv1_power_limits)
    )
    nv1_valid_count = int(nv1_valid.sum())

    duration_ok = (
        df["total_s"].gt(0) & df["charging_s"].gt(0) &
        df["charging_s"].le(df["total_s"])
    )
    after_duration = df.loc[duration_ok].copy()
    power = after_duration["energy_kwh"].div(after_duration["charging_h"])
    limits = after_duration["Port Type"].map(POWER_LIMITS_KW).fillna(POWER_LIMITS_KW["default"])
    power_ok = power.le(limits)
    after_power = after_duration.loc[power_ok].copy()

    start_local = parse_dates_robust(after_power["Start Date"])
    end_local = parse_dates_robust(after_power["End Date"])
    start_utc = convert_to_utc(start_local, after_power["Start Time Zone"])
    end_utc = convert_to_utc(end_local, after_power["End Time Zone"])
    observed_seconds = (end_utc - start_utc).dt.total_seconds()
    timestamp_ok = (
        after_power["total_s"].sub(observed_seconds).abs()
        .le(TIMESTAMP_TOLERANCE_SECONDS).fillna(False)
    )
    clean = after_power.loc[timestamp_ok].copy()
    clean["Station Name"] = (
        clean["Station Name"].astype("string").str.replace(r"\s+", " ", regex=True)
        .str.strip().str.replace("BRYANT # 1", "BRYANT #1", regex=False)
    )
    clean["idle_h"] = (clean["total_h"] - clean["charging_h"]).clip(lower=0)
    clean["idle_ratio"] = clean["idle_h"] / clean["total_h"]
    clean["chiem_dung_nghiem_trong"] = clean["idle_ratio"].gt(SEVERE_IDLE_RATIO).astype(int)

    stages = [
        ("Raw CSV rows", raw_rows, "Raw source rows"),
        ("After exact duplicate removal", after_dedup, "Exact duplicate rows removed"),
        ("After positive/consistent duration checks", len(after_duration),
         "Require total > 0, charging > 0, charging <= total"),
        ("After Port Type power limits", len(after_power),
         "Use POWER_LIMITS_KW from src.config by Port Type"),
        ("After timestamp consistency", len(clean),
         f"NV1 date parser + UTC; absolute duration difference <= {TIMESTAMP_TOLERANCE_SECONDS} seconds"),
    ]
    audit_rows = []
    prior = None
    for name, count, rule in stages:
        removed = None if prior is None else prior - count
        audit_rows.append({"stage": name, "rows_remaining": int(count),
                           "removed_at_stage": removed, "rule": rule})
        prior = count
    audit_rows.append({"stage": "NV1 is_valid_session (comparison)",
                       "rows_remaining": nv1_valid_count, "removed_at_stage": None,
                       "rule": "charging <= total and power <= configured Port Type limit"})
    audit_rows.append({"stage": "NV1-valid sessions excluded by NV4 timestamp check",
                       "rows_remaining": int((nv1_valid.reindex(after_power.index) & ~timestamp_ok).sum()),
                       "removed_at_stage": None,
                       "rule": "Only the additional NV4 timestamp consistency requirement"})
    audit = pd.DataFrame(audit_rows)
    metadata = {
        "raw_rows": raw_rows,
        "exact_duplicates_removed": raw_rows - after_dedup,
        "nv1_valid_sessions": nv1_valid_count,
        "nv4_valid_sessions": len(clean),
        "nv4_timestamp_rejected_after_other_checks": len(after_power) - len(clean),
        "power_limits_kw": {str(k): float(v) for k, v in POWER_LIMITS_KW.items()},
        "timestamp_tolerance_seconds": TIMESTAMP_TOLERANCE_SECONDS,
    }
    return clean.reset_index(drop=True), audit, metadata


def build_station_criteria(
    sessions: pd.DataFrame, min_sessions: int = MIN_STATION_SESSIONS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build all station criteria and the eligible ranking matrix."""
    required = {"Station Name", "energy_kwh", "charging_h", "idle_ratio", "chiem_dung_nghiem_trong"}
    missing = sorted(required - set(sessions.columns))
    if missing:
        raise ValueError(f"Missing prepared NV4 columns: {missing}")
    grouped = sessions.groupby("Station Name")
    all_stations = pd.DataFrame({
        "C1_so_phien": grouped.size(),
        "C2_tong_dien_nang": grouped["energy_kwh"].sum(),
        "C3_dien_nang_moi_phien": grouped["energy_kwh"].mean(),
        "C4_gio_sac_moi_phien": grouped["charging_h"].mean(),
        "C5_ty_le_nhan_roi": grouped["idle_ratio"].mean(),
        "C6_ty_le_chiem_dung_nghiem_trong": grouped["chiem_dung_nghiem_trong"].mean(),
        "C5_weighted": grouped["idle_h"].sum() / grouped["total_h"].sum(),
    }).round(6)
    eligible = all_stations.loc[all_stations["C1_so_phien"].ge(min_sessions)].sort_values(
        "C1_so_phien", ascending=False
    ).copy()
    return all_stations, eligible
