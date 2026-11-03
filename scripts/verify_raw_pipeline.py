import pandas as pd
import numpy as np

TRAN_CONG_SUAT_L2_KW = 19.2
NGUONG_PHIEN_TOI_THIEU = 500
NGUONG_CHIEM_DUNG = 0.5

def giay(s):
    try:
        h, m, gi = str(s).split(":")
        return int(h) * 3600 + int(m) * 60 + int(gi)
    except Exception:
        return np.nan

df = pd.read_csv("data/raw/EVChargingStationUsage.csv", encoding="utf-8-sig", low_memory=False)
print("Raw rows:", len(df))

df["total_s"] = df["Total Duration (hh:mm:ss)"].map(giay)
df["charging_s"] = df["Charging Time (hh:mm:ss)"].map(giay)
df["total_h"] = df["total_s"] / 3600
df["charging_h"] = df["charging_s"] / 3600
df["energy_kwh"] = pd.to_numeric(df["Energy (kWh)"], errors="coerce")

df = df.drop_duplicates()
print("After drop duplicates:", len(df))

hop_le_thoi_gian = (
    df["total_h"].gt(0) & df["charging_h"].gt(0) & df["charging_h"].le(df["total_h"])
)
df = df[hop_le_thoi_gian]
print("After time logic:", len(df))

df = df[(df["energy_kwh"] / df["charging_h"]).le(TRAN_CONG_SUAT_L2_KW)]
print("After power cap (19.2 kW):", len(df))

bat_dau = pd.to_datetime(df["Start Date"], errors="coerce")
ket_thuc = pd.to_datetime(df["End Date"], errors="coerce")
lech_giay = (df["total_s"] - (ket_thuc - bat_dau).dt.total_seconds()).abs()
df = df[lech_giay.le(59)]
print("After timestamp tolerance <= 59s:", len(df))

# Station name normalization
df["Station Name"] = (df["Station Name"].str.replace(r"\s+", " ", regex=True).str.strip()
                      .str.replace("BRYANT # 1", "BRYANT #1", regex=False))

distinct_stations = df["Station Name"].nunique()
print("Distinct station names:", distinct_stations)

station_counts = df.groupby("Station Name").size()
eligible_stations = station_counts[station_counts >= NGUONG_PHIEN_TOI_THIEU]
print("Eligible stations (>= 500):", len(eligible_stations))
print("Sessions in eligible stations:", eligible_stations.sum())

