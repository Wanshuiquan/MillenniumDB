#!/usr/bin/env python3
"""Plot execution-time distributions directly from benchmark db.log files."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
RESULTS_DIR = BASE_DIR / "results"
EXECUTION_RE = re.compile(r"^Execution\s*:\s*([0-9.eE+-]+)\s*ms")
MODES = ("light", "mid", "heavy")
MODE_LABELS = {"light": "LIGHT", "mid": "MID", "heavy": "HEAVY"}
MODE_COLORS = {"light": "#4C78A8", "mid": "#F58518", "heavy": "#54A24B"}
GROUPS = (
    ("lra", "complex", "LRA complex"),
    ("lia", "complex", "LIA complex"),
    ("nia", "simple", "NIA simple"),
    ("nia", "complex", "NIA complex"),
    ("nra", "simple", "NRA simple"),
    ("nra", "complex", "NRA complex"),
)


def execution_times(log_path: Path) -> list[float]:
    """Return only executions belonging to DATA_TEST queries.

    Each log also contains a candidate-selection query. The Match line tells
    us which following Execution entry belongs to the benchmark query.
    """
    times: list[float] = []
    is_data_test = False
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Match "):
            is_data_test = "DATA_TEST" in line
            continue
        if not is_data_test:
            continue
        match = EXECUTION_RE.match(line)
        if match:
            times.append(float(match.group(1)))
            is_data_test = False
    return times


def make_plot(dataset: str) -> Path:
    data: list[list[float]] = []
    positions: list[float] = []
    colors: list[str] = []
    group_centers: list[float] = []

    for group_index, (arithmetic, profile, _label) in enumerate(GROUPS):
        center = group_index * 1.4
        group_centers.append(center)
        for mode_index, mode in enumerate(MODES):
            path = LOG_DIR / dataset / arithmetic / profile / mode / "db.log"
            values = execution_times(path)
            if not values:
                raise RuntimeError(f"No DATA_TEST execution entries found in {path}")
            data.append(values)
            positions.append(center + (mode_index - 1) * 0.30)
            colors.append(MODE_COLORS[mode])

    fig, ax = plt.subplots(figsize=(14, 7.5))
    boxplot = ax.boxplot(
        data,
        positions=positions,
        widths=0.23,
        patch_artist=True,
        # Hide points beyond the 1.5-IQR whiskers so the distributions remain readable.
        showfliers=False,
        medianprops={"color": "#111111", "linewidth": 1.2},
        whiskerprops={"color": "#555555", "linewidth": 0.8},
        capprops={"color": "#555555", "linewidth": 0.8},
    )
    for patch, color in zip(boxplot["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.78)
        patch.set_edgecolor("#333333")

    ax.set_xticks(group_centers)
    ax.set_xticklabels([label for _arith, _profile, label in GROUPS])
    ax.set_ylabel("Execution time (ms)")
    ax.set_title(f"{dataset}: execution-time distributions from db.log")
    ax.grid(axis="y", which="both", linestyle=":", linewidth=0.6, alpha=0.65)
    ax.legend(
        handles=[
            Patch(facecolor=MODE_COLORS[mode], edgecolor="#333333", label=MODE_LABELS[mode])
            for mode in MODES
        ],
        title="Optimization mode",
        loc="upper right",
    )
    fig.text(
        0.01,
        0.01,
        "DATA_TEST queries only; candidate-selection executions excluded; outliers hidden",
        fontsize=8,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))

    output = RESULTS_DIR / f"{dataset}_execution_boxplot.png"
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return output


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for dataset in ("ldbc10", "pokec"):
        output = make_plot(dataset)
        print(output)


if __name__ == "__main__":
    main()
