"""
Generate template-level comparison figures per dataset from db.log.

Each figure has 2 subplots (LIA, NIA) and compares optimized vs naive
for templates T1..T12 using boxplots over running time (ms).

Template assignment is reconstructed from benchmark execution order:
for each template there are 6 query patterns, each with 1 warmup + 100 timed runs.

Output: results/figures/{dataset}_template_naive_vs_optimized.png
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

LOGS_DIR = Path(__file__).parent / "logs"
FIGURES_DIR = Path(__file__).parent / "results" / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

DATASETS = [
    ("ldbc01", "LDBC-01"),
    ("ldbc10", "LDBC-10"),
    ("pokec", "Pokec"),
    ("paradise", "Paradise"),
    ("telecom", "Telecom"),
    ("icij-leak", "ICIJ-Leak"),
]

TEMPLATES = list(range(1, 13))
COLOR_OPT = "#2E8B57"
COLOR_NAIVE = "#D2691E"

QUERIES_PER_TEMPLATE = 6
WARMUPS_PER_QUERY = 1
TIMED_RUNS_PER_QUERY = 100
POINTS_PER_TEMPLATE = QUERIES_PER_TEMPLATE * (WARMUPS_PER_QUERY + TIMED_RUNS_PER_QUERY)
EXPECTED_POINTS_PER_COMBO = 12 * POINTS_PER_TEMPLATE

RE_PARSER = re.compile(r"^Parser\s*:\s*([\d.]+)\s*ms", re.MULTILINE)
RE_OPTIMIZER = re.compile(r"^Optimizer\s*:\s*([\d.]+)\s*ms", re.MULTILINE)
RE_EXECUTION = re.compile(r"^Execution\s*:\s*([\d.]+)\s*ms", re.MULTILINE)
RE_TIMEOUT = re.compile(r"timed out after ([\d.]+) ms", re.MULTILINE)


def parse_running_times(log_path: Path) -> list[float]:
    with open(log_path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    blocks = re.split(r"(?=Query\(worker)", text)
    values: list[float] = []
    for block in blocks:
        if "Query(" not in block:
            continue

        t = RE_TIMEOUT.search(block)
        if t:
            values.append(float(t.group(1)))
            continue

        p = RE_PARSER.search(block)
        o = RE_OPTIMIZER.search(block)
        e = RE_EXECUTION.search(block)
        if p and o and e:
            values.append(float(p.group(1)) + float(o.group(1)) + float(e.group(1)))

    return values


def build_template_sequence(n_points: int) -> list[int]:
    seq: list[int] = []
    for t in TEMPLATES:
        seq.extend([t] * POINTS_PER_TEMPLATE)

    if n_points == len(seq):
        return seq
    if n_points < len(seq):
        return seq[:n_points]

    # If there are more points, repeat template cycles and then trim.
    reps = (n_points + len(seq) - 1) // len(seq)
    out = (seq * reps)[:n_points]
    return out


def load_dataset_points(dataset_key: str) -> pd.DataFrame:
    rows = []
    for arith in ("lia", "nia"):
        for variant in ("optimized", "naive"):
            log_path = LOGS_DIR / dataset_key / arith / variant / "db.log"
            if not log_path.exists():
                print(f"  Missing log: {log_path}")
                continue

            values = parse_running_times(log_path)
            if not values:
                continue

            # Keep only the latest benchmark block to avoid mixing old runs.
            if len(values) >= EXPECTED_POINTS_PER_COMBO:
                values = values[-EXPECTED_POINTS_PER_COMBO:]

            template_seq = build_template_sequence(len(values))

            for template_index, running_ms in zip(template_seq, values):
                rows.append(
                    {
                        "dataset": dataset_key,
                        "arithmetic": arith.upper(),
                        "variant": variant,
                        "template_index": template_index,
                        "running_ms": running_ms,
                    }
                )

    return pd.DataFrame(rows)


def make_template_figure(df: pd.DataFrame, display_name: str, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.8), sharey=False)

    offset = 0.18
    width = 0.30

    for col_idx, arithmetic in enumerate(("LIA", "NIA")):
        ax = axes[col_idx]
        sub = df[df["arithmetic"] == arithmetic]

        opt_vals = [
            sub[(sub["variant"] == "optimized") & (sub["template_index"] == t)]["running_ms"].tolist()
            for t in TEMPLATES
        ]
        naive_vals = [
            sub[(sub["variant"] == "naive") & (sub["template_index"] == t)]["running_ms"].tolist()
            for t in TEMPLATES
        ]

        bp_opt = ax.boxplot(
            opt_vals,
            positions=[t - offset for t in TEMPLATES],
            widths=width,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.2},
        )
        bp_naive = ax.boxplot(
            naive_vals,
            positions=[t + offset for t in TEMPLATES],
            widths=width,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.2},
        )

        for box in bp_opt["boxes"]:
            box.set(facecolor=COLOR_OPT, alpha=0.72)
        for box in bp_naive["boxes"]:
            box.set(facecolor=COLOR_NAIVE, alpha=0.72)

        ax.set_xticks(TEMPLATES)
        ax.set_xticklabels([f"T{t}" for t in TEMPLATES], fontsize=9)
        ax.set_yscale("log")
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)
        ax.set_title(arithmetic, fontsize=12)
        ax.set_xlabel("Query template", fontsize=10)
        ax.set_ylabel("Running time (ms, log scale)", fontsize=10)

        all_vals = [v for group in (opt_vals + naive_vals) for v in group]
        if all_vals:
            low = max(min(all_vals) / 2.0, 1e-3)
            high = max(all_vals) * 2.0
            if low < high:
                ax.set_ylim(low, high)

    opt_handle = plt.Line2D([0], [0], color=COLOR_OPT, lw=8, alpha=0.72)
    naive_handle = plt.Line2D([0], [0], color=COLOR_NAIVE, lw=8, alpha=0.72)
    fig.legend(
        [opt_handle, naive_handle],
        ["Optimized", "Naive"],
        loc="lower center",
        ncol=2,
        fontsize=10,
        framealpha=0.85,
        bbox_to_anchor=(0.5, -0.03),
    )

    fig.suptitle(
        f"{display_name}: Template-level comparison (T1-T12) - LIA & NIA\n"
        "(db.log-based running time; latest benchmark block per configuration)",
        fontsize=12,
    )

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def main() -> None:
    print(f"Output directory: {FIGURES_DIR}")
    for dataset_key, display_name in DATASETS:
        print(f"Generating template-level figure for {display_name}...")
        df = load_dataset_points(dataset_key)
        if df.empty:
            print(f"  Skipping {dataset_key}: no db.log points found")
            continue
        out_path = FIGURES_DIR / f"{dataset_key}_template_naive_vs_optimized.png"
        make_template_figure(df, display_name, out_path)
    print("Done.")


if __name__ == "__main__":
    main()
