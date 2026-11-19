"""Paired circular moving-block intervals for held-out NV5 occupancy errors."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MODELS = ("Persistence t-1", "XGBoost")


def daily_squared_errors(prediction_file):
    selected = []
    columns = ["cluster_id", "target", "model", "split", "timestamp_utc", "y_true", "y_pred"]
    for chunk in pd.read_csv(prediction_file, usecols=columns, chunksize=500_000):
        keep = (chunk.target.eq("occupancy_ports") & chunk["split"].eq("test")
                & chunk.model.isin(MODELS))
        if keep.any():
            selected.append(chunk.loc[keep])
    if not selected:
        raise ValueError("No occupancy test predictions for the requested models")
    frame = pd.concat(selected, ignore_index=True)
    frame["timestamp_utc"] = pd.to_datetime(frame.timestamp_utc, utc=True)
    wide = frame.pivot(index=["timestamp_utc", "cluster_id", "y_true"], columns="model", values="y_pred")
    if set(wide.columns) != set(MODELS) or wide.isna().any().any():
        raise ValueError("Missing matched forecasts or disagreeing observations")
    wide = wide.reset_index()
    if wide.duplicated(["timestamp_utc", "cluster_id"]).any():
        raise ValueError("Non-unique forecast pairs")
    active = wide.groupby("cluster_id").y_true.nunique().loc[lambda x: x.gt(1)].index
    wide = wide.loc[wide.cluster_id.isin(active)].copy()
    if wide.empty:
        raise ValueError("All targets are constant")
    for _, group in wide.groupby("cluster_id"):
        timestamps = group.timestamp_utc.sort_values()
        if (timestamps.iloc[0] != timestamps.iloc[0].normalize()
                or timestamps.iloc[-1] + pd.Timedelta(minutes=15) != timestamps.iloc[-1].ceil("D")
                or not timestamps.diff().dropna().eq(pd.Timedelta(minutes=15)).all()):
            raise ValueError("Bootstrap requires a complete UTC quarter-hour grid")
    wide["day"] = wide.timestamp_utc.dt.floor("D")
    for name in MODELS:
        wide[name] = (wide[name] - wide.y_true).pow(2)
    day_site = wide.groupby(["day", "cluster_id"])
    if not day_site.size().eq(96).all():
        raise ValueError("Expected 96 matched forecasts for each cluster and day")
    table = day_site[list(MODELS)].sum().unstack("cluster_id")
    if table.isna().any().any() or not table.index.to_series().diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("All sites must share one complete daily grid")
    # Columns are ordered by model, then by cluster.
    return table.to_numpy().reshape(len(table), len(MODELS), len(active)), active


def bootstrap(daily, block_days, replicates, seed):
    day_count = len(daily)
    if not 1 <= block_days <= day_count:
        raise ValueError("Invalid block length")
    rng = np.random.default_rng(seed)
    block_count = (day_count + block_days - 1) // block_days
    starts = rng.integers(day_count, size=(replicates, block_count, 1))
    indices = ((starts + np.arange(block_days)) % day_count).reshape(replicates, -1)[:, :day_count]
    # Chunk the replicates to keep the working set small.
    rmse = np.concatenate([
        np.sqrt(daily[idx].sum(axis=1) / (96 * day_count)).mean(axis=2)
        for idx in np.array_split(indices, max(1, (replicates + 499) // 500))
    ])
    differences = rmse[:, 1] - rmse[:, 0]
    reductions = 100 * (1 - rmse[:, 1] / rmse[:, 0])
    baseline, xgb = np.sqrt(daily.sum(axis=0) / (96 * day_count)).mean(axis=1)
    return {
        "block_days": block_days, "replicates": replicates, "seed": seed,
        "utc_days": day_count, "clusters": daily.shape[-1],
        "rmse_persistence": baseline, "rmse_xgboost": xgb,
        "difference_xgb_minus_persistence": xgb - baseline,
        "difference_p025": np.quantile(differences, .025), "difference_p975": np.quantile(differences, .975),
        "reduction_pct": 100 * (1 - xgb / baseline),
        "reduction_pct_p025": np.quantile(reductions, .025), "reduction_pct_p975": np.quantile(reductions, .975),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    daily, active = daily_squared_errors(args.run_dir / "baseline_predictions.csv")
    estimates = pd.DataFrame([bootstrap(daily, k, 10_000, 42) for k in (1, 7, 14)])
    out = args.run_dir / "robustness" / "occupancy_block_bootstrap.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    estimates.to_csv(out, index=False)
    print("Nonconstant test clusters:", ", ".join(active))
    print(estimates.round(6).to_string(index=False))
    print(out)


if __name__ == "__main__":
    main()
