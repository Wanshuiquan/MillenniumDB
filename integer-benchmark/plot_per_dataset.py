"""
Generate one comparison figure per dataset: aggregated boxplots comparing naive vs optimized
for LIA and NIA, grouped by query category (Frequently-used, Occasionally-used, Rarely-used).
One figure per dataset, 2 subplots (LIA left, NIA right). Overwrites existing per-dataset figures.
"""

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

DATASETS = [
    ("ldbc01", "ldbc01_lia_nia_trial.csv", "LDBC-01"),
    ("ldbc10", "ldbc10_lia_nia_trial.csv", "LDBC-10"),
    ("pokec", "pokec_lia_nia_trial.csv", "Pokec"),
    ("paradise", "paradise_lia_nia_trial.csv", "Paradise"),
    ("telecom", "telecom_lia_nia_trial.csv", "Telecom"),
    ("icij-leak", "icij-leak_lia_nia_trial.csv", "ICIJ-Leak"),
]

CATEGORIES = ["Frequently-used", "Occasionally-used", "Rarely-used"]
CAT_SHORT = ["Frequent", "Occasional", "Rare"]

COLOR_OPT = "#2E8B57"
COLOR_NAIVE = "#D2691E"


def table3_category(template_index: int) -> str:
    if 1 <= template_index <= 4:
        return "Frequently-used"
    if 5 <= template_index <= 7:
        return "Occasionally-used"
    if 8 <= template_index <= 12:
        return "Rarely-used"
    raise ValueError(f"Unexpected template index: {template_index}")


def make_figure(dataset_key, csv_file, display_name):
    path = RESULTS_DIR / csv_file
    if not path.exists():
        print(f"  Skipping {dataset_key}: file not found ({path})")
        return

    df = pd.read_csv(path)
    df["category"] = df["template_index"].apply(table3_category)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=False)

    centers = [1, 2, 3]
    offset = 0.20
    width = 0.34

    for col_idx, arithmetic in enumerate(["LIA", "NIA"]):
        ax = axes[col_idx]
        sub = df[df["arithmetic"] == arithmetic]

        opt_vals = [
            sub[(sub["variant"] == "optimized") & (sub["category"] == c)]["median_ms"].tolist() for c in CATEGORIES
        ]
        naive_vals = [
            sub[(sub["variant"] == "naive") & (sub["category"] == c)]["median_ms"].tolist() for c in CATEGORIES
        ]

        bp_opt = ax.boxplot(
            opt_vals,
            positions=[c - offset for c in centers],
            widths=width,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.4},
        )
        bp_naive = ax.boxplot(
            naive_vals,
            positions=[c + offset for c in centers],
            widths=width,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.4},
        )

        for box in bp_opt["boxes"]:
            box.set(facecolor=COLOR_OPT, alpha=0.70)
        for box in bp_naive["boxes"]:
            box.set(facecolor=COLOR_NAIVE, alpha=0.70)

        ax.set_xticks(centers)
        ax.set_xticklabels(CAT_SHORT, fontsize=10)
        ax.set_yscale("log")
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)
        ax.set_title(f"{arithmetic}", fontsize=12)
        ax.set_ylabel("Median latency (ms, log scale)", fontsize=10)

        all_vals = [v for g in opt_vals + naive_vals for v in g]
        if all_vals:
            low = max(min(all_vals) / 2, 1e-3)
            high = max(all_vals) * 2
            if low < high:
                ax.set_ylim(low, high)

    opt_handle = plt.Line2D([0], [0], color=COLOR_OPT, lw=9, alpha=0.70)
    naive_handle = plt.Line2D([0], [0], color=COLOR_NAIVE, lw=9, alpha=0.70)
    fig.legend(
        [opt_handle, naive_handle],
        ["Optimized", "Naive"],
        loc="lower center",
        ncol=2,
        fontsize=10,
        framealpha=0.85,
        bbox_to_anchor=(0.5, -0.04),
    )

    fig.suptitle(
        f"{display_name}: Naive vs Optimized — LIA & NIA\n"
        "(boxplots by query category; y = median latency per query)",
        fontsize=12,
    )

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out_path = FIGURES_DIR / f"{dataset_key}_naive_vs_optimized.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def main():
    print(f"Output directory: {FIGURES_DIR}")
    for dataset_key, csv_file, display_name in DATASETS:
        print(f"Generating figure for {display_name}...")
        make_figure(dataset_key, csv_file, display_name)
    print("Done.")


if __name__ == "__main__":
    main()
