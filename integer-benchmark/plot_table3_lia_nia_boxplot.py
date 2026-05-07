#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


def table3_category(template_index: int) -> str:
    # Table 3 in evaluation/paper_draft/main.pdf:
    # Q1-Q4: Frequently-used, Q5-Q7: Occasionally-used, Q8-Q12: Rarely-used
    if 1 <= template_index <= 4:
        return "Frequently-used"
    if 5 <= template_index <= 7:
        return "Occasionally-used"
    if 8 <= template_index <= 12:
        return "Rarely-used"
    raise ValueError(f"Unexpected template index: {template_index}")


def init_bucket() -> dict[str, dict[str, dict[str, list[float]]]]:
    return {
        "LIA": {
            "optimized": {
                "Frequently-used": [],
                "Occasionally-used": [],
                "Rarely-used": [],
            },
            "naive": {
                "Frequently-used": [],
                "Occasionally-used": [],
                "Rarely-used": [],
            },
        },
        "NIA": {
            "optimized": {
                "Frequently-used": [],
                "Occasionally-used": [],
                "Rarely-used": [],
            },
            "naive": {
                "Frequently-used": [],
                "Occasionally-used": [],
                "Rarely-used": [],
            },
        },
    }


def collect_runtime_points(
    results_dir: Path,
) -> dict[str, dict[str, dict[str, dict[str, list[float]]]]]:
    data: dict[str, dict[str, dict[str, dict[str, list[float]]]]] = {}

    for csv_path in sorted(results_dir.glob("*_lia_nia_trial.csv")):
        with csv_path.open("r", encoding="utf-8") as fin:
            reader = csv.DictReader(fin)
            for row in reader:
                dataset = row["dataset"].strip()
                arithmetic = row["arithmetic"].strip().upper()
                if arithmetic not in {"LIA", "NIA"}:
                    continue
                variant = row["variant"].strip().lower()
                if variant not in {"optimized", "naive"}:
                    continue

                if dataset not in data:
                    data[dataset] = init_bucket()

                template_index = int(row["template_index"])
                category = table3_category(template_index)
                # Use median runtime per query pattern as a robust aggregate point.
                median_ms = float(row["median_ms"])
                data[dataset][arithmetic][variant][category].append(median_ms)

    return data


def draw_split_boxplot(data: dict[str, dict[str, dict[str, dict[str, list[float]]]]], out_path: Path) -> None:
    categories = ["Frequently-used", "Occasionally-used", "Rarely-used"]
    datasets = sorted(data.keys())
    arithmetics = ["LIA", "NIA"]

    n_rows = len(datasets)
    n_cols = len(arithmetics)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6.8 * n_cols, 3.8 * n_rows),
        squeeze=False,
        sharey=False,
    )

    centers = [1, 2, 3]
    offset = 0.18
    width = 0.30

    for row_idx, dataset in enumerate(datasets):
        for col_idx, arithmetic in enumerate(arithmetics):
            ax = axes[row_idx][col_idx]

            optimized_values = [data[dataset][arithmetic]["optimized"][c] for c in categories]
            naive_values = [data[dataset][arithmetic]["naive"][c] for c in categories]

            bp_opt = ax.boxplot(
                optimized_values,
                positions=[c - offset for c in centers],
                widths=width,
                patch_artist=True,
                showfliers=True,
                medianprops={"color": "black", "linewidth": 1.2},
            )
            bp_naive = ax.boxplot(
                naive_values,
                positions=[c + offset for c in centers],
                widths=width,
                patch_artist=True,
                showfliers=True,
                medianprops={"color": "black", "linewidth": 1.2},
            )

            for box in bp_opt["boxes"]:
                box.set(facecolor="#2E8B57", alpha=0.65)
            for box in bp_naive["boxes"]:
                box.set(facecolor="#D2691E", alpha=0.65)

            ax.set_xticks(centers)
            ax.set_xticklabels(categories)
            ax.set_yscale("log")
            ax.grid(True, axis="y", linestyle="--", alpha=0.35)
            ax.set_title(f"{dataset} | {arithmetic}")
            ax.set_ylabel("Median Runtime (ms)")

            # Keep lower bound positive for log scale even when medians are tiny.
            all_values = [v for group in optimized_values + naive_values for v in group]
            if all_values:
                min_v = min(all_values)
                max_v = max(all_values)
                low = max(min_v / 1.6, 1e-4)
                high = max_v * 1.5
                if low < high:
                    ax.set_ylim(low, high)

    opt_handle = plt.Line2D([0], [0], color="#2E8B57", lw=8, alpha=0.65)
    naive_handle = plt.Line2D([0], [0], color="#D2691E", lw=8, alpha=0.65)
    fig.legend(
        [opt_handle, naive_handle],
        ["optimized", "naive"],
        loc="lower center",
        ncol=2,
        framealpha=0.85,
        bbox_to_anchor=(0.5, 0.005),
    )

    fig.suptitle(
        "Table 3 Category Runtime Distributions Split by Dataset and Arithmetic\n"
        "(Boxplots compare optimized vs naive; metric = median_ms per query pattern)",
        y=0.992,
        fontsize=12,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def draw_aggregated_boxplot(data: dict[str, dict[str, dict[str, dict[str, list[float]]]]], out_path: Path) -> None:
    categories = ["Frequently-used", "Occasionally-used", "Rarely-used"]
    arithmetics = ["LIA", "NIA"]

    # Aggregate all datasets together for a high-level Table 3 view.
    aggregated: dict[str, dict[str, dict[str, list[float]]]] = {
        "LIA": {
            "optimized": {c: [] for c in categories},
            "naive": {c: [] for c in categories},
        },
        "NIA": {
            "optimized": {c: [] for c in categories},
            "naive": {c: [] for c in categories},
        },
    }

    for dataset in data:
        for arithmetic in arithmetics:
            for variant in ["optimized", "naive"]:
                for category in categories:
                    aggregated[arithmetic][variant][category].extend(data[dataset][arithmetic][variant][category])

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8), squeeze=False, sharey=False)

    centers = [1, 2, 3]
    offset = 0.18
    width = 0.30

    for col_idx, arithmetic in enumerate(arithmetics):
        ax = axes[0][col_idx]
        optimized_values = [aggregated[arithmetic]["optimized"][c] for c in categories]
        naive_values = [aggregated[arithmetic]["naive"][c] for c in categories]

        bp_opt = ax.boxplot(
            optimized_values,
            positions=[c - offset for c in centers],
            widths=width,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.2},
        )
        bp_naive = ax.boxplot(
            naive_values,
            positions=[c + offset for c in centers],
            widths=width,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.2},
        )

        for box in bp_opt["boxes"]:
            box.set(facecolor="#2E8B57", alpha=0.65)
        for box in bp_naive["boxes"]:
            box.set(facecolor="#D2691E", alpha=0.65)

        ax.set_xticks(centers)
        ax.set_xticklabels(categories)
        ax.set_yscale("log")
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)
        ax.set_title(f"{arithmetic}")
        ax.set_ylabel("Median Runtime (ms)")

        all_values = [v for group in optimized_values + naive_values for v in group]
        if all_values:
            min_v = min(all_values)
            max_v = max(all_values)
            low = max(min_v / 1.6, 1e-4)
            high = max_v * 1.5
            if low < high:
                ax.set_ylim(low, high)

    opt_handle = plt.Line2D([0], [0], color="#2E8B57", lw=8, alpha=0.65)
    naive_handle = plt.Line2D([0], [0], color="#D2691E", lw=8, alpha=0.65)
    fig.legend(
        [opt_handle, naive_handle],
        ["optimized", "naive"],
        loc="lower center",
        ncol=2,
        framealpha=0.85,
        bbox_to_anchor=(0.5, 0.005),
    )

    fig.suptitle(
        "Table 3 Category Runtime Distributions (All Datasets Aggregated)\n"
        "(Boxplots compare optimized vs naive; metric = median_ms per query pattern)",
        y=0.992,
        fontsize=12,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "integer-benchmark" / "results"
    out_split_path = results_dir / "figures" / "table3_split_dataset_arith_naive_vs_optimized_boxplot.png"
    out_agg_path = results_dir / "figures" / "table3_lia_nia_aggregated_boxplot.png"

    data = collect_runtime_points(results_dir)

    for dataset in sorted(data):
        print(f"Dataset: {dataset}")
        for arithmetic in ["LIA", "NIA"]:
            for variant in ["optimized", "naive"]:
                counts = []
                for category in ["Frequently-used", "Occasionally-used", "Rarely-used"]:
                    counts.append(len(data[dataset][arithmetic][variant][category]))
                print(f"  {arithmetic}-{variant}: " f"F={counts[0]}, O={counts[1]}, R={counts[2]}, total={sum(counts)}")

    draw_aggregated_boxplot(data, out_agg_path)
    print(f"Saved figure: {out_agg_path}")

    draw_split_boxplot(data, out_split_path)
    print(f"Saved figure: {out_split_path}")


if __name__ == "__main__":
    main()
