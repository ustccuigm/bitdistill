"""Render paper experiment figures from the organized CSV tables."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


METHODS = ["BF16", "GPTQ", "EfficientQAT", "BitDistiller", "On-Policy QAD", "QeRL", "Ours"]
COLORS = dict(zip(METHODS, ["#707070", "#1f77b4", "#ff7f0e", "#8c564b", "#d62728", "#9467bd", "#1b8f3a"]))
MODELS = ["Qwen3-8B", "Qwen3.5-4B", "Gemma 4 12B-it"]
BENCHMARKS = ["bfcl_v4", "tau2_bench", "webshop", "alfworld", "search_qa"]
BENCHMARK_LABELS = ["BFCL V4", "tau2-Bench", "WebShop", "ALFWorld", "Search QA"]


def read(data, name):
    with (data / f"{name}.csv").open(newline="") as stream:
        return list(csv.DictReader(stream))


def save(fig, output, name):
    for extension in ("pdf", "png"):
        fig.savefig(output / f"{name}.{extension}", dpi=200, bbox_inches="tight")
    plt.close(fig)


def style(ax, xlabel=None, ylabel=None):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=.2)
    ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)


def results(data, output):
    rows = read(data, "benchmark_results")
    quantized = [row for row in rows if row["precision"] in ("BF16", "W4A16")]
    chart_colors = ["#9da3a6", "#829bab", "#b7a47c", "#a29aa9",
                    "#739c96", "#c0957b", "#a33a31"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.9), sharey=True)
    fig.subplots_adjust(left=.045, right=.99, bottom=.23, top=.78, wspace=.14)
    fig.text(.045, .965, "Average benchmark score (%)", fontsize=11,
             color="#555b60", va="top")
    fig.text(.99, .965, "Three models / seven methods", fontsize=10,
             color="#777c80", ha="right", va="top")
    for model, ax in zip(MODELS, axes):
        values = [next(float(row["average"]) for row in quantized
                       if row["model"] == model and row["method"] == method)
                  for method in METHODS]
        bars = ax.bar(range(len(METHODS)), [value-40 for value in values],
                      bottom=40, width=.61, color=chart_colors, zorder=3)
        for bar, value, method in zip(bars, values, METHODS):
            ax.annotate(f"{value:.2f}",
                        (bar.get_x()+bar.get_width()/2, value),
                        xytext=(0, 6), textcoords="offset points",
                        ha="center", fontsize=9.5,
                        color="#a33a31" if method == "Ours" else "#4c5155",
                        fontweight="bold" if method == "Ours" else "normal")
        ax.set_xticks([])
        ax.set_title(model, fontsize=14, fontfamily="DejaVu Serif",
                     color="#292825", pad=20)
        ax.set_ylim(40, 70)
        ax.set_yticks(range(40, 71, 5))
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#cfd3d5")
        ax.tick_params(axis="y", length=0, labelsize=9, colors="#777c80", pad=8)
        ax.grid(axis="y", color="#e9ebed", linewidth=.65)
        ax.set_axisbelow(True)
        # Mark the nonzero baseline explicitly, including on panels without ticks.
        ax.plot([-.018, -.006, .006, .018], [-.012, .012, -.012, .012],
                transform=ax.transAxes, color="#777c80", linewidth=1,
                clip_on=False)
    legend = fig.legend(bars, METHODS, ncol=7, loc="lower center",
                        bbox_to_anchor=(.52, .08), frameon=False, fontsize=10,
                        handlelength=1, handleheight=.8, columnspacing=1.9)
    legend.get_texts()[-1].set_color("#a33a31")
    legend.get_texts()[-1].set_fontweight("bold")
    fig.savefig(output / "model_comparison.svg", bbox_inches="tight")
    save(fig, output, "model_comparison")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), layout="constrained")
    for model, ax in zip(MODELS, axes):
        for index, method in enumerate(METHODS):
            row = next(row for row in quantized if row["model"] == model and row["method"] == method)
            ax.bar([x + (index-3)*.11 for x in range(5)], [float(row[key]) for key in BENCHMARKS],
                   width=.105, color=COLORS[method], label=method)
        ax.set_xticks(range(5), BENCHMARK_LABELS, rotation=30, ha="right")
        ax.set_title(model)
        ax.set_ylim(0, 100)
        style(ax, ylabel="Score (%)")
    axes[1].legend(ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.35), frameon=False)
    save(fig, output, "benchmark_comparison")


def scatter(ax, rows, precision):
    for method in METHODS:
        row = next(row for row in rows if row["precision"] == precision and row["method"] == method)
        ax.scatter(float(row["output_tokens"]), float(row["pass_at_1"]),
                   color=COLORS[method], s=45, label=method, zorder=3)
    style(ax, "Output tokens per successful task", "Pass@1 (%)")
    ax.set_title(precision)
    ax.margins(.12)


def efficiency(data, output):
    rows = read(data, "training_efficiency")
    points = read(data, "inference_efficiency")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for method in ("On-Policy QAD", "QeRL", "Ours", "BF16"):
        curve = [row for row in rows if row["method"] == method]
        x, y = [float(row["gpu_hours"]) for row in curve], [float(row["mean"]) for row in curve]
        axes[0].plot(x, y, "--" if method == "BF16" else "o-", color=COLORS[method], label=method, markersize=3)
        if method != "BF16":
            axes[0].fill_between(x, [float(row["lower"]) for row in curve],
                                 [float(row["upper"]) for row in curve], color=COLORS[method], alpha=.12)
    style(axes[0], "Cumulative GPU hours", "Pass@1 (%)")
    axes[0].set_title("Training efficiency")
    axes[0].legend(frameon=False, fontsize=8)
    scatter(axes[1], points, "W4A16")
    axes[1].legend(ncol=2, frameon=False, fontsize=8)
    save(fig, output, "figure_03_efficiency")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for ax, precision in zip(axes, ("W2A16", "W4A8")):
        scatter(ax, points, precision)
        ax.legend(ncol=2, frameon=False, fontsize=8)
    save(fig, output, "figure_04_efficiency")


def heatmap(ax, matrix, rows, columns, *, maximum=100):
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=maximum, aspect="auto")
    ax.set_xticks(range(len(columns)), columns, rotation=35, ha="right")
    ax.set_yticks(range(len(rows)), rows)
    for y, values in enumerate(matrix):
        for x, value in enumerate(values):
            ax.text(x, y, f"{value:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if value > maximum*.6 else "black")
    return image


def diagnostics(data, output):
    rows = read(data, "ablations")
    fig, ax = plt.subplots(figsize=(10, 7), layout="constrained")
    labels = [row["configuration"] for row in rows]
    ax.barh(range(len(rows)), [float(row["overall"]) for row in rows],
            color=[COLORS["Ours"] if row["group"] == "Full" else "#6688a1" for row in rows])
    ax.set_yticks(range(len(rows)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 50)
    for index, row in enumerate(rows):
        ax.text(float(row["overall"])+.2, index, row["overall"], va="center", fontsize=8)
    style(ax, "BFCL V4 Overall (%)")
    save(fig, output, "ablation_comparison")

    rows = read(data, "additional_metrics")
    columns = list(rows[0])[1:]
    fig, ax = plt.subplots(figsize=(12, 4.5), layout="constrained")
    image = heatmap(ax, [[float(row[col]) for col in columns] for row in rows],
                    [row["method"] for row in rows], columns)
    fig.colorbar(image, ax=ax, label="Score (%)")
    save(fig, output, "additional_metrics")

    rows = read(data, "reasoning_prefix")
    labels = list(rows[0])[2:]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
    for ax, case in zip(axes, ("door_locking", "file_ordering")):
        selected = [row for row in rows if row["case"] == case]
        image = heatmap(ax, [[float(row[col]) for col in labels] for row in selected],
                        [row["weights_label"] for row in selected], labels, maximum=1)
        ax.set_title(case.replace("_", " ").title())
        ax.set_xlabel("Reasoning prefix source")
        ax.set_ylabel("Model weights")
    fig.colorbar(image, ax=list(axes), label="Verified correct-action probability")
    save(fig, output, "figure_08_reasoning_prefix")

    rows = read(data, "inference_statistics")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
    for ax, key in zip(axes, ("output_tokens", "interaction_steps", "tool_calls")):
        ax.barh(METHODS, [float(row[key]) for row in rows], color=[COLORS[m] for m in METHODS])
        ax.invert_yaxis()
        style(ax, key.replace("_", " ").title() + " per successful task")
    save(fig, output, "inference_statistics")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="CSV directory from the gh-pages experiment collection")
    parser.add_argument("--output", type=Path, required=True, help="Destination for generated PDF and PNG figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    results(args.data, args.output)
    efficiency(args.data, args.output)
    diagnostics(args.data, args.output)
    manifest = {"matplotlib_version": matplotlib.__version__, "inputs": {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(args.data.glob("*.csv"))
    }, "figures": sorted(path.name for path in args.output.iterdir() if path.suffix in (".png", ".pdf"))}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved 8 figures as PDF and PNG to {args.output}")


if __name__ == "__main__":
    main()
