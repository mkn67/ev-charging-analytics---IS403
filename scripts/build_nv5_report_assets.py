"""Rebuild section 4.5 tables and figures from a single audited NV5 run."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


TARGETS = ("occupancy_ports", "session_arrivals")
MODELS = ("Historical Mean", "Persistence t-1", "Persistence Day t-96",
          "Persistence Week t-672", "Ridge", "Random Forest", "XGBoost")
GROUPS = ("Lag ngắn hạn", "Lag ngày/tuần", "Trung bình trượt", "Lịch")
TZ = "America/Los_Angeles"
COLORS = ("#17324d", "#00796b", "#b75b16")


def error_summary(df, keys):
    error = df.y_pred - df.y_true
    by_cluster = df.assign(ae=error.abs(), se=error.pow(2), error=error).groupby(
        [*keys, "model", "cluster_id"], observed=True
    ).agg(n=("error", "size"), MAE=("ae", "mean"), mse=("se", "mean"), bias=("error", "mean"))
    by_cluster["RMSE"] = by_cluster.pop("mse").pow(0.5)
    return by_cluster.groupby([*keys, "model"], observed=True).agg(
        n=("n", "sum"), MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), bias=("bias", "mean"))


def save(fig, out, name):
    fig.savefig(out / name, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def importance_assets(run, out):
    d = pd.read_csv(run / "feature_importance.csv")
    d["group"] = np.select(
        [d.feature.isin(["lag_1", "lag_2", "lag_4"]), d.feature.isin(["lag_96", "lag_672"]),
         d.feature.str.startswith("rolling_")], GROUPS[:3], default=GROUPS[3])
    positive = d.groupby(["cluster_id", "target"]).gain_normalized.transform("sum") > 0
    d = d.loc[positive].copy()
    d["gain_pct"] = 100 * d.gain_normalized
    sums = d.groupby(["target", "cluster_id", "group"]).gain_pct.sum()
    summary = sums.groupby(["target", "group"]).agg(["mean", "min", "max"])
    summary.to_csv(out / "Bảng 4.5.8 - gain theo nhóm.csv", encoding="utf-8-sig")
    d.groupby(["target", "feature"]).gain_pct.agg(["mean", "min", "max"]).to_csv(
        out / "Gain theo từng đặc trưng.csv", encoding="utf-8-sig")
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.5), sharey=True, layout="constrained")
    for ax, target, title in zip(axes, TARGETS, ("Số cổng có phiên kết nối", "Số phiên bắt đầu")):
        values = summary.loc[target, "mean"].reindex(GROUPS)
        ax.barh(GROUPS, values, color=COLORS[1] if target == TARGETS[0] else COLORS[0])
        ax.bar_label(ax.containers[0], labels=[f"{v:.1f}%".replace(".", ",") for v in values], padding=4)
        ax.set_title(title, loc="left", fontweight="bold", fontsize=11)
        ax.set(xlim=(0, 110), xlabel="Tỷ trọng gain trung bình (%)")
        ax.grid(axis="x", alpha=0.18)
    axes[0].invert_yaxis()
    save(fig, out, "Hình 4.5.1 - Gain theo nhóm.png")


def weekly_figure(predictions, out, split, start, end, number, label):
    start_local, end_local = (pd.Timestamp(value, tz=TZ) for value in (start, end))
    fig, axes = plt.subplots(2, 1, figsize=(12.2, 5.4), sharex=True, layout="constrained")
    for ax, target, ylabel, baseline in zip(axes, TARGETS, ("Số cổng", "Số phiên / 15 phút"),
                                          ("Persistence t-1", "Historical Mean")):
        subset = predictions.loc[(predictions.cluster_id.eq("BRYANT")) & (predictions["split"].eq(split))
                                 & (predictions.target.eq(target))]
        frame = subset.pivot(index="timestamp_utc", columns="model", values="y_pred")
        actual = subset.loc[subset.model.eq("XGBoost")].set_index("timestamp_utc").y_true
        frame["Quan sát"] = actual
        frame.index = frame.index.tz_convert(TZ)
        frame = frame.loc[(frame.index >= start_local) & (frame.index < end_local)].sort_index()
        assert len(frame) == 672 and not frame[["Quan sát", "XGBoost", baseline]].isna().any().any()
        for col, color, width in zip(("Quan sát", "XGBoost", baseline), COLORS, (1.25, 1.0, 0.85)):
            ax.plot(frame.index, frame[col], color=color, linewidth=width, label=col,
                    alpha=0.85 if col != "Quan sát" else 1)
        ax.set(ylabel=ylabel, xlim=(start_local, end_local))
        ax.legend(loc="upper right", ncol=3, frameon=False, fontsize=8)
        ax.grid(alpha=0.17)
    axes[-1].xaxis.set_major_locator(mdates.DayLocator(tz=start_local.tz))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m", tz=start_local.tz))
    axes[-1].set_xlabel("Giờ địa phương Palo Alto")
    fig.suptitle(f"BRYANT · {label}", x=.055, ha="left", fontweight="bold")
    save(fig, out, f"Hình 4.5.{number} - BRYANT {start[:4]}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    run = args.run
    out = run / "bao_cao_4_5"
    out.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    m = pd.read_csv(run / "nv5_model_comparison.csv")
    for number, split in ((2, "test"), (5, "stress_2020")):
        wide = m.loc[m["split"].eq(split)].groupby(["model", "target"])[["MAE", "RMSE", "R2"]].mean().unstack()
        wide.reindex(MODELS).swaplevel(axis=1).reindex(
            columns=pd.MultiIndex.from_product([TARGETS, ("MAE", "RMSE", "R2")])
        ).to_csv(out / f"Bảng 4.5.{number} - tổng hợp.csv", encoding="utf-8-sig")

    test = m.loc[m["split"].eq("test")]
    for number, target, baseline in zip((3, 4), TARGETS, ("Persistence t-1", "Historical Mean")):
        t = test.loc[test.target.eq(target)]
        xgb = t.loc[t.model.eq("XGBoost"), ["cluster_id", "MAE", "RMSE", "R2"]].set_index("cluster_id")
        xgb["RMSE_baseline"] = t.loc[t.model.eq(baseline)].set_index("cluster_id").RMSE
        xgb["RMSE_reduction_pct"] = 100 * (1 - xgb.RMSE / xgb.RMSE_baseline.replace(0, np.nan))
        xgb["lowest_RMSE_model"] = t.sort_values("RMSE").drop_duplicates("cluster_id").set_index("cluster_id").model
        xgb.loc[xgb.RMSE_baseline.eq(0) & xgb.RMSE.eq(0), "lowest_RMSE_model"] = "tie (0)"
        xgb.to_csv(out / f"Bảng 4.5.{number} - theo cụm.csv", encoding="utf-8-sig")

    parts = []
    for c in pd.read_csv(run / "baseline_predictions.csv", chunksize=400_000):
        use = (c["split"].eq("test") & c.target.eq(TARGETS[0])
               | c.cluster_id.eq("BRYANT") & c["split"].eq("test") & c.target.eq(TARGETS[1])
               | c.cluster_id.eq("BRYANT") & c["split"].eq("stress_2020"))
        if use.any():
            parts.append(c.loc[use])
    preds = pd.concat(parts, ignore_index=True)
    preds["timestamp_utc"] = pd.to_datetime(preds.timestamp_utc, utc=True)
    occ = preds.loc[preds["split"].eq("test") & preds.target.eq(TARGETS[0])]
    active = test.loc[test.target.eq(TARGETS[0]) & ~test.constant_target, "cluster_id"].unique()
    occ = occ.loc[occ.cluster_id.isin(active)].copy()
    persist = occ.loc[occ.model.eq("Persistence t-1"), ["cluster_id", "timestamp_utc", "y_pred"]]
    occ = occ.merge(persist.rename(columns={"y_pred": "previous"}), on=["cluster_id", "timestamp_utc"], validate="many_to_one")
    occ["state"] = np.where(occ.y_true.eq(occ.previous), "Giữ nguyên", "Thay đổi")
    error_summary(occ.loc[occ.model.isin(("XGBoost", "Persistence t-1"))], ["state"]).to_csv(
        out / "Bảng 4.5.6 - occupancy theo trạng thái.csv", encoding="utf-8-sig")

    series = pd.read_csv(run / "timeseries_15min.csv", usecols=["cluster_id", "timestamp_utc", TARGETS[0]])
    series["timestamp_utc"] = pd.to_datetime(series.timestamp_utc, utc=True)
    train_rows = test.train_rows.unique()
    if len(train_rows) != 1:
        raise ValueError("Expected the same training grid for every cluster")
    train_end = pd.to_datetime(test.train_end_utc.unique().item(), utc=True)
    train = series.loc[series.timestamp_utc.lt(train_end)].sort_values("timestamp_utc").groupby("cluster_id").tail(int(train_rows[0]))
    thresholds = train.groupby("cluster_id")[TARGETS[0]].quantile(.90)
    occ["high_threshold"] = occ.cluster_id.map(thresholds)
    high = occ.loc[occ.y_true.ge(occ.high_threshold)]
    error_summary(high, []).to_csv(out / "Bảng 4.5.9 - chiếm dụng cao.csv", encoding="utf-8-sig")
    thresholds.to_csv(out / "Ngưỡng phân vị 90 theo cụm.csv", encoding="utf-8-sig")

    bryant = occ.loc[occ.cluster_id.eq("BRYANT") & occ.model.eq("XGBoost")].copy()
    local = bryant.timestamp_utc.dt.tz_convert(TZ)
    bryant["hour"] = local.dt.hour
    bryant["day_type"] = np.where(local.dt.dayofweek < 5, "Ngày làm việc", "Cuối tuần")
    hourly = bryant.groupby(["hour", "day_type"]).y_true.mean().unstack()
    hourly.to_csv(out / "BRYANT - quan sát theo giờ.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(9.5, 3.65), layout="constrained")
    for name, color in zip(("Ngày làm việc", "Cuối tuần"), COLORS):
        ax.plot(hourly.index, hourly[name], "o-", color=color, linewidth=2, markersize=4, label=name)
    ax.set(xlabel="Giờ địa phương Palo Alto", ylabel="Số cổng trung bình",
           xticks=range(0, 24, 2), xlim=(0, 23), ylim=(0, None))
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.2)
    save(fig, out, "Hình 4.5.4 - BRYANT theo giờ.png")
    importance_assets(run, out)
    weekly_figure(preds, out, "test", "2019-08-12", "2019-08-19", 2, "12–18/08/2019")
    weekly_figure(preds, out, "stress_2020", "2020-08-10", "2020-08-17", 3, "10–16/08/2020")
    print(out.resolve())


if __name__ == "__main__":
    main()
