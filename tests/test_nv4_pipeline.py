import pandas as pd

from src.nv4_analysis import build_station_criteria, prepare_nv4_sessions


def source_row(station, start, end, zone_start, zone_end, duration, energy, port_type="Level 2"):
    return {
        "Station Name": station,
        "Start Date": start,
        "End Date": end,
        "Start Time Zone": zone_start,
        "End Time Zone": zone_end,
        "Total Duration (hh:mm:ss)": duration,
        "Charging Time (hh:mm:ss)": duration,
        "Energy (kWh)": energy,
        "Port Type": port_type,
    }


def test_nv4_pipeline_dedup_duration_config_power_and_nv1_utc_time_check():
    normal = source_row("Station A", "01/01/2020 00:00", "01/01/2020 00:30",
                        "PST", "PST", "00:30:00", 3.6)
    dst_crossing = source_row("Station B", "03/08/2020 01:30", "03/08/2020 03:30",
                              "PST", "PDT", "01:00:00", 7.2)
    duration_mismatch = source_row("Station C", "01/01/2020 00:00", "01/01/2020 01:00",
                                   "PST", "PST", "00:30:00", 3.6)
    level1_over_limit = source_row("Station D", "01/01/2020 00:00", "01/01/2020 01:00",
                                   "PST", "PST", "01:00:00", 6.0, "Level 1")
    raw = pd.DataFrame([normal, normal, dst_crossing, duration_mismatch, level1_over_limit])

    clean, ledger, metadata = prepare_nv4_sessions(raw)
    assert len(clean) == 2
    assert set(clean["Station Name"]) == {"Station A", "Station B"}
    assert metadata["exact_duplicates_removed"] == 1
    assert metadata["nv1_valid_sessions"] == 3
    assert metadata["nv4_timestamp_rejected_after_other_checks"] == 1
    assert ledger.loc[ledger.stage.eq("After Port Type power limits"), "removed_at_stage"].iloc[0] == 1
    assert ledger.loc[ledger.stage.eq("After timestamp consistency"), "removed_at_stage"].iloc[0] == 1


def test_criteria_threshold_is_applied_after_session_reconciliation():
    sessions = pd.DataFrame({
        "Station Name": ["A"] * 500 + ["B"] * 499,
        "energy_kwh": [2.0] * 999,
        "charging_h": [1.0] * 999,
        "idle_h": [1.0] * 999,
        "total_h": [2.0] * 999,
        "idle_ratio": [0.5] * 999,
        "chiem_dung_nghiem_trong": [0] * 999,
    })
    all_stations, eligible = build_station_criteria(sessions)
    assert len(all_stations) == 2
    assert eligible.index.tolist() == ["A"]
    assert eligible.loc["A", "C1_so_phien"] == 500
    assert "C5_weighted" in all_stations
