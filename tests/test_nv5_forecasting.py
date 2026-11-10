"""NV5 tests: source IDs, physical port occupancy, boundaries and cluster isolation."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "05_NV5_demand_forecasting.ipynb"
notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
nv5_namespace = {}
for cell in notebook["cells"]:
    tags = cell.get("metadata", {}).get("tags", [])
    if cell["cell_type"] == "code" and "nv5-audit" not in tags and "nv5-run" not in tags:
        exec("".join(cell["source"]), nv5_namespace)
nv5 = SimpleNamespace(**{name: value for name, value in nv5_namespace.items() if not name.startswith("__")})


def sessions(rows):
    base = {"is_valid_session": True, "cluster_id": "A", "Energy (kWh)": 1.0}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_two_overlapping_sessions_on_same_port_count_once():
    d = sessions([
        {"start_datetime_utc": "2020-01-01 00:00", "end_datetime_utc": "2020-01-01 00:15", "port_id": "p1"},
        {"start_datetime_utc": "2020-01-01 00:05", "end_datetime_utc": "2020-01-01 00:20", "port_id": "p1"},
    ])
    s, _ = nv5.make_regular_series(d)
    assert s.occupancy_ports.tolist() == [1, 1]
    assert s.session_arrivals.tolist() == [2, 0]


def test_two_distinct_ports_count_two_and_end_boundary_is_exclusive():
    d = sessions([
        {"start_datetime_utc": "2020-01-01 00:00", "end_datetime_utc": "2020-01-01 00:15", "port_id": "p1"},
        {"start_datetime_utc": "2020-01-01 00:00", "end_datetime_utc": "2020-01-01 00:30", "port_id": "p2"},
    ])
    s, info = nv5.make_regular_series(d)
    assert s.occupancy_ports.tolist() == [2, 1]
    assert s.session_arrivals.tolist() == [2, 0]
    assert s.timestamp_utc.tolist() == list(pd.date_range("2020-01-01 00:00", periods=2, freq="15min"))
    assert not info["occupancy_exceeds_observed_ports"]


def test_each_cluster_has_own_zero_filled_grid_and_port_limit():
    d = sessions([
        {"cluster_id": "A", "start_datetime_utc": "2020-01-01 00:00", "end_datetime_utc": "2020-01-01 00:15", "port_id": "a1"},
        {"cluster_id": "B", "start_datetime_utc": "2020-01-01 00:30", "end_datetime_utc": "2020-01-01 00:45", "port_id": "b1"},
    ])
    s, info = nv5.make_regular_series(d)
    assert set(s.cluster_id) == {"A", "B"}
    assert s.groupby("cluster_id").size().to_dict() == {"A": 3, "B": 3}
    assert s.loc[s.cluster_id.eq("A"), "occupancy_ports"].tolist() == [1, 0, 0]
    assert s.loc[s.cluster_id.eq("B"), "occupancy_ports"].tolist() == [0, 0, 1]
    assert not info["occupancy_exceeds_observed_ports"]


def test_missing_port_id_is_excluded_from_occupancy_but_arrival_is_counted():
    d = sessions([{
        "start_datetime_utc": "2020-01-01 00:00", "end_datetime_utc": "2020-01-01 00:30",
        "port_id": pd.NA,
    }])
    s, _ = nv5.make_regular_series(d)
    assert s.occupancy_ports.tolist() == [0, 0]
    assert s.session_arrivals.tolist() == [1, 0]


def test_port_id_must_match_mac_plus_port_mapping(tmp_path):
    d = pd.DataFrame({
        "MAC Address": ["aa:bb"], "Port Number": [1], "port_id": ["aa:bb_Port_1"],
        "Station Name": ["PALO ALTO CA / BRYANT #1"],
    })
    path = tmp_path / "mapping.csv"
    pd.DataFrame({"station_name": ["PALO ALTO CA / BRYANT #1"], "cluster_id": ["BRYANT"]}).to_csv(path, index=False)
    result = nv5.attach_clusters(d, path)
    assert result.loc[0, "cluster_id"] == "BRYANT"
    d.loc[0, "port_id"] = "1"
    with pytest.raises(ValueError, match="disagrees"):
        nv5.attach_clusters(d, path)


def test_station_name_mapping_handles_a_port_relocated_between_sites(tmp_path):
    d = pd.DataFrame({
        "MAC Address": ["aa:bb", "aa:bb"], "Port Number": [1, 1],
        "port_id": ["aa:bb_Port_1", "AABB_Port_1"],
        "Station Name": ["PALO ALTO CA / HAMILTON #2", "PALO ALTO CA / BRYANT #3"],
    })
    path = tmp_path / "mapping.csv"
    pd.DataFrame({
        "station_name": ["PALO ALTO CA / HAMILTON #2", "PALO ALTO CA / BRYANT #3"],
        "cluster_id": ["HAMILTON", "BRYANT"],
    }).to_csv(path, index=False)
    result = nv5.attach_clusters(d, path)
    assert result.port_id.nunique() == 1
    assert result.cluster_id.tolist() == ["HAMILTON", "BRYANT"]


def test_station_cluster_map_requires_one_cluster_per_station_name(tmp_path):
    d = pd.DataFrame({
        "MAC Address": ["aa", "bb"], "Port Number": [1, 1],
        "Station Name": ["PALO ALTO CA / BRYANT #1", "PALO ALTO CA / BRYANT #2"],
    })
    path = tmp_path / "mapping.csv"
    pd.DataFrame({
        "station_name": ["PALO ALTO CA / BRYANT #1", "PALO ALTO CA / BRYANT #1"],
        "cluster_id": ["BRYANT", "HAMILTON"],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError, match="exactly one cluster_id"):
        nv5.attach_clusters(d, path)


def test_lags_and_rolling_features_are_cluster_local_and_past_only():
    timestamps = pd.date_range("2020-01-01", periods=700, freq="15min")
    a = pd.DataFrame({"cluster_id": "A", "timestamp_utc": timestamps,
                      "occupancy_ports": np.arange(700, dtype=float)})
    b = a.copy()
    b["cluster_id"] = "B"
    b["occupancy_ports"] += 10000
    f = nv5.add_features(pd.concat([a, b], ignore_index=True), "occupancy_ports")
    fa = f.loc[f.cluster_id.eq("A")].reset_index(drop=True)
    fb = f.loc[f.cluster_id.eq("B")].reset_index(drop=True)
    assert fa.loc[0, "lag_1"] == 671
    assert fa.loc[0, "lag_2"] == 670
    assert fa.loc[0, "rolling_mean_4"] == np.mean([668, 669, 670, 671])
    assert fa.loc[0, "rolling_mean_12"] == np.mean(np.arange(660, 672))
    assert fb.loc[0, "lag_96"] == fa.loc[0, "lag_96"] + 10000
    assert fb.loc[0, "rolling_mean_4"] == fa.loc[0, "rolling_mean_4"] + 10000


def test_split_milestones_are_required_in_chronological_order():
    with pytest.raises(ValueError, match="train_end_utc"):
        nv5._parse_splits({"train_end_utc": "2020-03-01", "validation_end_utc": "2020-02-01",
                           "test_end_utc": "2020-04-01"})


def test_ridge_scaler_is_fit_on_train_only():
    train = pd.DataFrame({"x": [0.0, 2.0], "y": [1.0, 3.0]})
    validation = pd.DataFrame({"x": [100.0], "y": [0.0]})
    test = pd.DataFrame({"x": [-100.0], "y": [0.0]})
    _, _, scaler = nv5.ridge_predictions(train, validation, test, ["x"], "y")
    assert scaler.mean_.tolist() == [1.0]


def test_port_ids_normalize_mac_format_and_case():
    values = pd.Series(["aa:bb_Port_1", "AABB_Port_1"])
    assert nv5._normalize_port_id(values).tolist() == ["AABB_Port_1", "AABB_Port_1"]


def test_count_forecasts_are_clipped_to_physical_port_limit():
    assert nv5.clip_to_port_limit([-2, 1.5, 9], 4).tolist() == [0.0, 1.5, 4.0]
    # Arrivals are sessions, so do not cap them by the number of physical ports.
    assert nv5.clip_to_port_limit([-1, 3, 8]).tolist() == [0.0, 3.0, 8.0]


def test_stress_test_boundary_is_optional_and_must_follow_test():
    base = {"train_end_utc": "2019-01-01", "validation_end_utc": "2019-07-01",
            "test_end_utc": "2020-01-01"}
    assert nv5._parse_splits(base)[3] is None
    with pytest.raises(ValueError, match="stress_start_utc"):
        nv5._parse_splits({**base, "stress_start_utc": "2019-12-01"})
    assert nv5._parse_splits({**base, "stress_start_utc": "2020-01-01"})[3] == pd.Timestamp("2020-01-01")


def test_run_target_emits_separate_stress_metrics(monkeypatch):
    class FakeXGBRegressor:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def fit(self, x, y):
            self.value = float(np.mean(y))
            return self

        def predict(self, x):
            return np.full(len(x), self.value)

    monkeypatch.setitem(sys.modules, "xgboost", SimpleNamespace(XGBRegressor=FakeXGBRegressor))
    timestamps = pd.date_range("2020-01-01", periods=800, freq="15min")
    series = pd.DataFrame({
        "cluster_id": "A", "timestamp_utc": timestamps,
        "occupancy_ports": (np.arange(800) % 5).astype(float),
        "observed_physical_ports": 5,
    })
    splits = {
        "train_end_utc": timestamps[710],
        "validation_end_utc": timestamps[750],
        "test_end_utc": timestamps[775],
        "stress_start_utc": timestamps[780],
    }
    scores, predictions = nv5.run_target(series, "occupancy_ports", splits)
    stress_scores = scores.loc[scores.split.eq("stress_2020")]
    assert len(stress_scores) == 7
    assert predictions.loc[predictions.split.eq("stress_2020"), "timestamp_utc"].nunique() == 20
    assert stress_scores.test_end_utc.nunique() == 1
