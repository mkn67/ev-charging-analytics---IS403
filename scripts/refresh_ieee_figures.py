"""Re-export IEEE charts at their print widths using saved NV3–NV5 results."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
COLUMN = 3.44
BLUE = "#234e70"
TEAL = "#00806c"
ORANGE = "#a65216"
TZ = "America/Los_Angeles"


def cliff_intervals(data, out):
    metrics = ("T_idle_min", "Idle_Ratio_check", "Energy", "T_charging")
    labels = ("Giờ nhàn rỗi", "Tỷ lệ nhàn rỗi", "Điện năng", "Thời gian sạc")
    data = data.set_index("Metric").loc[list(metrics)]
    intervals = data["CI 95% (Cluster)"].str.extract(
        r"\[\s*([-.\d]+),\s*([-.\d]+)\s*\]"
    ).astype(float)
    delta = data.Delta.to_numpy()
    positions = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(COLUMN, 1.8), layout="constrained")
    ax.axvline(0, color="#788590", linewidth=0.8)
    for point in (-0.147, 0.147):
        ax.axvline(point, color=ORANGE, linestyle=":", linewidth=0.9)
    ax.errorbar(delta, positions, xerr=[delta - intervals[0], intervals[1] - delta],
                color=BLUE, fmt="o", markersize=3.5, capsize=3, linewidth=1.2)
    ax.set(yticks=positions, yticklabels=labels, xlim=(-0.175, 0.175),
           ylim=(3.5, -0.5), xlabel="Cliff’s Delta và khoảng tin cậy 95%")
    ax.set_xticks([-0.15, -0.075, 0, 0.075, 0.15],
                  ["−0,15", "−0,075", "0", "0,075", "0,15"])
    fig.savefig(out / "cliff_intervals.pdf")
    plt.close(fig)


def idle_threshold(data, out):
    values = data.set_index("Giai đoạn").loc[
        ["Pre-policy", "Post-policy"], ["Tỷ lệ [15-20p) (%)", "Tỷ lệ [20-25p) (%)"]
    ].to_numpy()
    x = np.arange(2)
    fig, ax = plt.subplots(figsize=(COLUMN, 1.82), layout="constrained")
    for index, (label, color, hatch) in enumerate((("Trước mốc", BLUE, ""), ("Sau mốc", ORANGE, "//"))):
        bars = ax.bar(x + (index - 0.5) * 0.34, values[index], width=0.32, label=label,
                      color=color, hatch=hatch, edgecolor=color)
        ax.bar_label(bars, labels=[f"{v:.2f}%".replace(".", ",") for v in values[index]], padding=2)
    ax.set(xticks=x, xticklabels=["[15, 20) phút", "[20, 25) phút"], ylabel="Tỷ lệ phiên (%)",
           ylim=(0, 4.7), yticks=range(5))
    ax.legend(loc="upper center", ncols=2, frameon=False)
    fig.savefig(out / "idle_threshold.pdf")
    plt.close(fig)


def rank_sensitivity(data, out):
    cases = data.iloc[1:]
    labels = cases.Scenario.str.split(":").str[0]
    fig, ax = plt.subplots(figsize=(COLUMN, 1.7), layout="constrained")
    ax.plot(labels, cases.Spearman_Entropy, color=BLUE, marker="o", label="Spearman")
    ax.plot(labels, cases.Kendall_Entropy, color=TEAL, marker="s", linestyle="--", label="Kendall")
    ax.set(ylim=(0.65, 1.1), yticks=[0.7, 0.8, 0.9, 1], ylabel="Tương quan với S0",
           xlabel="Kịch bản độ nhạy")
    ax.grid(axis="y", alpha=0.18)
    ax.legend(loc="lower left", ncols=2, frameon=False)
    fig.savefig(out / "rank_sensitivity.pdf")
    plt.close(fig)


def feature_gain(data, out):
    groups = ["Lag ngắn hạn", "Lag ngày/tuần", "Trung bình trượt", "Lịch"]
    values = data.pivot(index="group", columns="target", values="mean").loc[groups]
    y = np.arange(len(groups))
    fig, ax = plt.subplots(figsize=(COLUMN, 2.05), layout="constrained")
    for index, (key, label, color) in enumerate((
        ("occupancy_ports", "Số cổng", TEAL), ("session_arrivals", "Lượt bắt đầu", BLUE)
    )):
        ax.barh(y + (index - 0.5) * 0.34, values[key], height=0.3, color=color, label=label)
    ax.set(yticks=y, yticklabels=groups, xticks=[0, 20, 40, 60, 80], xlim=(0, 86),
           ylim=(3.65, -1.3), xlabel="Tỷ trọng gain trung bình (%)")
    ax.grid(axis="x", alpha=0.16)
    ax.legend(loc="upper center", ncols=2, frameon=False)
    fig.savefig(out / "gain.pdf")
    plt.close(fig)


def weekly_predictions(run, out):
    windows = [
        ("test", "2019-08-12", "2019-08-19", out.parent / "paper_bryant_week_2019.png"),
        ("stress_2020", "2020-08-10", "2020-08-17", out / "bryant_stress.pdf"),
    ]
    models = ("XGBoost", "Persistence t-1", "Historical Mean")
    parts = []
    columns = ["cluster_id", "target", "model", "split", "timestamp_utc", "y_true", "y_pred"]
    for chunk in pd.read_csv(run / "baseline_predictions.csv", usecols=columns, chunksize=400_000):
        keep = chunk.cluster_id.eq("BRYANT") & chunk["split"].isin(("test", "stress_2020")) & chunk.model.isin(models)
        parts.append(chunk.loc[keep])
    predictions = pd.concat(parts, ignore_index=True)
    predictions["timestamp_utc"] = pd.to_datetime(predictions.timestamp_utc, utc=True).dt.tz_convert(TZ)
    for split, start, end, path in windows:
        start, end = pd.Timestamp(start, tz=TZ), pd.Timestamp(end, tz=TZ)
        week = predictions.loc[predictions["split"].eq(split) & predictions.timestamp_utc.ge(start)
                               & predictions.timestamp_utc.lt(end)]
        fig, axes = plt.subplots(2, 1, figsize=(6.1, 2.74), sharex=True, layout="constrained")
        for ax, target, baseline, unit in zip(
            axes, ("occupancy_ports", "session_arrivals"), models[1:], ("Số cổng", "Số phiên")
        ):
            subset = week.loc[week.target.eq(target)]
            frame = subset.pivot(index="timestamp_utc", columns="model", values="y_pred").sort_index()
            frame["Quan sát"] = subset.loc[subset.model.eq("XGBoost")].set_index("timestamp_utc").y_true
            if len(frame) != 7 * 96 or frame[["Quan sát", "XGBoost", baseline]].isna().any().any():
                raise ValueError(f"Missing aligned BRYANT predictions for {target} in {split}")
            for label, color, style in (
                ("Quan sát", BLUE, "-"), (baseline, ORANGE, "--"), ("XGBoost", TEAL, "-")
            ):
                ax.plot(frame.index, frame[label], color=color, linestyle=style, label=label,
                        linewidth=0.72, alpha=0.88)
            ax.set(ylabel=unit, xlim=(start, end), ylim=(0, 1.35 * frame.max().max() + 0.1))
            ax.legend(loc="upper left", ncols=3, frameon=False)
            ax.grid(alpha=0.15)
        axes[-1].xaxis.set_major_locator(mdates.DayLocator(tz=start.tz))
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m", tz=start.tz))
        axes[-1].set_xlabel("Ngày theo giờ Palo Alto")
        fig.savefig(path, dpi=320)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "figures")
    args = parser.parse_args()
    out = args.output_dir / "paper_extended"
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.labelsize": 8.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5, "pdf.fonttype": 42,
    })
    nv3 = ROOT / "notebooks" / "outputs_nv3_v6"
    cliff_intervals(pd.read_csv(nv3 / "3.3.3_stats.csv"), out)
    idle_threshold(pd.read_csv(nv3 / "3.3.4_bunching.csv"), out)
    rank_sensitivity(pd.read_csv(ROOT / "outputs" / "nv4_sensitivity_analysis.csv"), out)
    feature_gain(pd.read_csv(args.run / "bao_cao_4_5" / "Bảng 4.5.8 - gain theo nhóm.csv"), out)
    weekly_predictions(args.run, out)


if __name__ == "__main__":
    main()
