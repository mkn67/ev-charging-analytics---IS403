import json
from pathlib import Path

import pandas as pd
import pytest
from scipy.stats import kendalltau, spearmanr

from src.nv4_analysis import build_station_criteria, build_station_rankings, prepare_nv4_sessions
from src.topsis import entropy_weights, normalize_minmax, topsis


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


def ranking_inputs():
    criteria = pd.DataFrame(
        {"C1_so_phien": [500, 700, 600]}, index=["Station B", "Station C", "Station A"]
    )
    entropy = pd.DataFrame(
        {"TOPSIS_Score": [0.8, 0.2, 0.5], "Rank": [1, 3, 2]},
        index=["Station C", "Station A", "Station B"],
    )
    equal = pd.DataFrame(
        {"TOPSIS_Score": [0.6, 0.9, 0.3], "Rank": [2, 1, 3]},
        index=["Station A", "Station B", "Station C"],
    )
    criteria.columns.name = "Tiêu chí"
    return criteria, entropy, equal


def test_station_rankings_align_independently_ordered_inputs_by_station_name():
    criteria, entropy, equal = ranking_inputs()
    result = build_station_rankings(criteria, entropy, equal)

    assert result.columns.name is None
    assert result["Station Name"].tolist() == ["Station C", "Station B", "Station A"]
    assert result["C1_so_phien"].tolist() == [700, 500, 600]
    assert result["Score_Entropy"].tolist() == [0.8, 0.5, 0.2]
    assert result["Rank_Entropy"].tolist() == [1, 2, 3]
    assert result["Score_Equal"].tolist() == [0.3, 0.9, 0.6]
    assert result["Rank_Equal"].tolist() == [3, 1, 2]
    assert result["Rank_Diff"].tolist() == [2, 1, 1]
    pd.testing.assert_frame_equal(
        result,
        build_station_rankings(criteria.iloc[::-1], entropy.iloc[::-1], equal.iloc[::-1]),
    )


def test_notebook_ranks_stations_by_name_when_score_and_session_orders_differ():
    notebook = Path(__file__).resolve().parents[1] / "notebooks" / "04_NV4_station_benchmarking.ipynb"
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    code = ("".join(cell["source"]) for cell in cells if cell["cell_type"] == "code")
    ranking_source = next(source for source in code if "top_entropy = topsis(" in source)
    criteria = pd.DataFrame(
        {"C1_so_phien": [900, 700, 500], "C2_tong_dien_nang": [1, 10, 2]},
        index=["Station C", "Station B", "Station A"],
    )
    scope = {
        "X": criteria,
        "decision": criteria,
        "criterion_columns": list(criteria.columns),
        "directions": dict.fromkeys(criteria.columns, 1),
        "labels": {column: column for column in criteria.columns},
        "pd": pd,
        "normalize_minmax": normalize_minmax,
        "entropy_weights": entropy_weights,
        "topsis": topsis,
        "build_station_rankings": build_station_rankings,
        "spearmanr": spearmanr,
        "kendalltau": kendalltau,
        "display": lambda _: None,
    }
    exec(ranking_source, scope)
    ranking = scope["df_rank"].set_index("Station Name")

    for label, results in (("Entropy", scope["top_entropy"]), ("Equal", scope["top_equal"])):
        assert not results.index.equals(criteria.index)
        assert results["Rank"].idxmin() == "Station B"
        pd.testing.assert_series_equal(
            ranking[f"Rank_{label}"], results["Rank"].reindex(ranking.index), check_names=False,
        )
        pd.testing.assert_series_equal(
            ranking[f"Score_{label}"], results["TOPSIS_Score"].reindex(ranking.index), check_names=False,
        )


def test_station_rankings_reject_missing_or_different_station_identifiers():
    criteria, entropy, equal = ranking_inputs()
    with pytest.raises(ValueError, match="cover exactly"):
        build_station_rankings(criteria, entropy.iloc[:-1], equal)
    different = equal.rename(index={"Station A": "Unknown Station"})
    with pytest.raises(ValueError, match="cover exactly"):
        build_station_rankings(criteria, entropy, different)


def test_station_rankings_reject_duplicate_station_identifiers_and_missing_values():
    criteria, entropy, equal = ranking_inputs()
    duplicates = pd.concat([entropy, entropy.iloc[:1]])
    with pytest.raises(ValueError, match="unique station"):
        build_station_rankings(criteria, duplicates, equal)
    duplicate_criteria = pd.concat([criteria, criteria.iloc[:1]])
    with pytest.raises(ValueError, match="unique station"):
        build_station_rankings(duplicate_criteria, entropy, equal)
    missing_score = equal.copy()
    missing_score.loc["Station A", "TOPSIS_Score"] = float("nan")
    with pytest.raises(ValueError, match="populated"):
        build_station_rankings(criteria, entropy, missing_score)
