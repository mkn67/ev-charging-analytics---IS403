"""Run the two historical occupancy windows and score stored arrivals forecasts."""

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/05_NV5_demand_forecasting.ipynb"
WINDOWS = {
    "2018_H2": ("2018-01-01", "2018-07-01", "2019-01-01"),
    "2019_H1": ("2018-07-01", "2019-01-01", "2019-07-01"),
}
OCCUPANCY_MODELS = ("XGBoost", "Persistence t-1")
ARRIVALS_MODELS = ("XGBoost", "Random Forest", "Historical Mean")
SPLIT_KEYS = ("train_end_utc", "validation_end_utc", "test_end_utc")


def load_forecast_runner():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    namespace = {}
    for cell in notebook["cells"]:
        if "nv5-definitions" in cell["metadata"].get("tags", []):
            exec(compile("".join(cell["source"]), str(NOTEBOOK), "exec"), namespace)
    return namespace["run_target"]


def score_arrivals(source, out):
    columns = ["timestamp_utc", "cluster_id", "split", "target", "model", "y_true", "y_pred"]
    pieces = []
    for chunk in pd.read_csv(source / "baseline_predictions.csv", usecols=columns, chunksize=400_000):
        mask = (chunk.target.eq("session_arrivals") & chunk["split"].eq("test")
                & chunk.model.isin(ARRIVALS_MODELS))
        if mask.any():
            pieces.append(chunk.loc[mask])
    if not pieces:
        raise ValueError("No saved arrival forecasts for test")
    predictions = pd.concat(pieces, ignore_index=True)
    keys = ["cluster_id", "timestamp_utc", "y_true"]
    matched = predictions.pivot(index=keys, columns="model", values="y_pred")
    if set(matched.columns) != set(ARRIVALS_MODELS) or matched.isna().any().any():
        raise ValueError("Arrivals models must share the same timestamps and observations")
    matched = matched.reset_index()
    if matched.duplicated(keys[:2]).any():
        raise ValueError("Duplicate arrivals cluster/timestamp")
    active = matched.groupby("cluster_id").y_true.nunique().gt(1)
    matched = matched.loc[matched.cluster_id.isin(active[active].index)].copy()
    if matched.empty:
        raise ValueError("No nonconstant test clusters for arrivals")
    matched["Always zero"] = 0.0
    matched["actual_group"] = matched.y_true.clip(upper=2).astype(int).map({0: "0", 1: "1", 2: "2+"})

    records = []
    for model in (*ARRIVALS_MODELS, "Always zero"):
        group = matched[["cluster_id", "actual_group"]].assign(error=matched[model] - matched.y_true)
        for label, subset in [("all", group), *group.groupby("actual_group")]:
            for cluster, rows in subset.groupby("cluster_id"):
                error = rows.error
                records.append({"model": model, "actual_group": label, "cluster_id": cluster,
                                "bins": len(error), "MAE": error.abs().mean(),
                                "RMSE": (error.pow(2).mean()) ** .5, "bias": error.mean()})
    detail = pd.DataFrame(records)
    summary = detail.groupby(["actual_group", "model"], as_index=False).agg(
        bins=("bins", "sum"), clusters=("cluster_id", "nunique"),
        MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), bias=("bias", "mean"))
    detail.to_csv(out / "arrivals_by_cluster.csv", index=False)
    summary.to_csv(out / "arrivals_summary.csv", index=False)
    print(summary.round(4).to_string(index=False), flush=True)


def score_occupancy(source, out):
    run_target = load_forecast_runner()
    series = pd.read_csv(source / "timeseries_15min.csv", parse_dates=["timestamp_utc"],
                         usecols=["cluster_id", "timestamp_utc", "occupancy_ports"])
    test_rows, validation_rows = [], []
    for name, dates in WINDOWS.items():
        splits = dict(zip(SPLIT_KEYS, dates))
        print(f"Occupancy {name}: train, validation, test end at {dates} UTC", flush=True)
        history = series.loc[series.timestamp_utc.lt(pd.Timestamp(dates[-1]))]
        scores, _ = run_target(history, "occupancy_ports", splits, models=OCCUPANCY_MODELS)
        validation_rows.extend({"window": name, **row} for row in scores.attrs["candidates"])
        scores.attrs = {}
        test_rows.append(scores.loc[scores["split"].eq("test")].assign(window=name))
    detail = pd.concat(test_rows, ignore_index=True)
    active = detail.loc[~detail.constant_target]
    summary = active.groupby(["window", "model"], as_index=False).agg(
        clusters=("cluster_id", "nunique"), MAE=("MAE", "mean"), RMSE=("RMSE", "mean"),
        R2=("R2", "mean"))
    errors = summary.pivot(index="window", columns="model", values="RMSE")
    summary["xgboost_rmse_gain_pct"] = summary.window.map(
        100 * (1 - errors["XGBoost"] / errors["Persistence t-1"]))
    detail.to_csv(out / "occupancy_by_cluster.csv", index=False)
    summary.to_csv(out / "occupancy_summary.csv", index=False)
    pd.DataFrame(validation_rows).to_csv(out / "occupancy_validation_candidates.csv", index=False)
    print(summary.round(4).to_string(index=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="NV5 run with series and saved predictions")
    args = parser.parse_args()
    out = args.run_dir / "robustness"
    out.mkdir(parents=True, exist_ok=True)
    score_arrivals(args.run_dir, out)
    score_occupancy(args.run_dir, out)


if __name__ == "__main__":
    main()
