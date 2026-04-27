#!/usr/bin/env python3
"""Benchmark comparison for telecom, ldbc10, and pokec.

Compares optimized query performance between:
- evaluation/case-study/<dataset>/optimized
- evaluation/old-case-study/<dataset>/optimized

Outputs:
- CSV summaries under evaluation/figure/improving-benchmarking
- PDF plots under evaluation/figure/improving-benchmarking
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "case-study"
OLD_ROOT = ROOT / "old-case-study"
OUT_ROOT = ROOT / "figure" / "improving-benchmarking"

DATASETS = ["telecom", "ldbc10", "pokec"]
VARIANT_ORDER = ["data-1", "data-2", "data-3", "data-4", "data-5", "no-data"]
FLOAT_RE = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def parse_db_log(path: Path) -> list[float]:
    """Extract total time per query execution from db.log as parser+optimizer+execution ms."""
    text = path.read_text(errors="ignore")
    chunks = re.findall(r"Query\(worker.*?(?=\nQuery\(worker|\Z)", text, flags=re.DOTALL)

    totals: list[float] = []
    for chunk in chunks:
        parser_ms = optimizer_ms = execution_ms = np.nan

        m = re.search(rf"Parser\s*:\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            parser_ms = float(m.group(1))

        m = re.search(rf"Optimizer\s*:\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            optimizer_ms = float(m.group(1))

        m = re.search(rf"Execution\s*:\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            execution_ms = float(m.group(1))

        if not any(np.isnan(v) for v in [parser_ms, optimizer_ms, execution_ms]):
            totals.append(parser_ms + optimizer_ms + execution_ms)

    return totals


def collect_rows(dataset: str, base: Path, version_label: str) -> list[dict]:
    rows: list[dict] = []
    root = base / dataset / "optimized"
    if not root.exists():
        print(f"Warning: missing path: {root}")
        return rows

    q_dirs = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("Q")], key=lambda p: int(p.name[1:]))
    for q in q_dirs:
        for variant in VARIANT_ORDER:
            log = q / variant / "db.log"
            if not log.exists():
                continue
            totals = parse_db_log(log)
            for total_ms in totals:
                rows.append(
                    {
                        "dataset": dataset,
                        "version": version_label,
                        "query": q.name,
                        "variant": variant,
                        "total_ms": total_ms,
                    }
                )
    return rows


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["dataset", "version", "query", "variant"], as_index=False)["total_ms"]
        .agg(median="median", mean="mean", min="min", max="max", count="count")
    )
    return grouped


def build_speedup(summary: pd.DataFrame) -> pd.DataFrame:
    pivot = summary.pivot_table(
        index=["dataset", "query", "variant"],
        columns="version",
        values="median",
        aggfunc="first",
    ).reset_index()

    if "case-study" not in pivot.columns or "old-case-study" not in pivot.columns:
        return pd.DataFrame()

    pivot["speedup_old_over_new"] = pivot["old-case-study"] / pivot["case-study"]
    return pivot


def save_tables(summary: pd.DataFrame, speedup: pd.DataFrame) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_ROOT / "summary_median_mean_min_max.csv", index=False)
    if not speedup.empty:
        speedup.to_csv(OUT_ROOT / "speedup_old_over_new.csv", index=False)


def plot_dataset_boxplots(df: pd.DataFrame) -> None:
    for dataset in DATASETS:
        sub = df[df["dataset"] == dataset].copy()
        if sub.empty:
            continue

        queries = sorted(sub["query"].unique(), key=lambda q: int(q[1:]))
        cols = 4
        rows = int(np.ceil(len(queries) / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.5, rows * 3.5))
        axes = np.array(axes).reshape(-1)

        for ax, query in zip(axes, queries):
            qsub = sub[sub["query"] == query].copy()
            qsub["variant"] = pd.Categorical(qsub["variant"], categories=VARIANT_ORDER, ordered=True)
            sns.boxplot(
                data=qsub,
                x="variant",
                y="total_ms",
                hue="version",
                order=VARIANT_ORDER,
                showfliers=False,
                palette=["#4c78a8", "#f58518"],
                ax=ax,
            )
            ax.set_yscale("log")
            ax.set_title(query)
            ax.set_xlabel("")
            ax.set_ylabel("Total ms")
            ax.tick_params(axis="x", rotation=30, labelsize=8)
            leg = ax.get_legend()
            if leg:
                leg.remove()

        for ax in axes[len(queries):]:
            ax.set_visible(False)

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", ncol=2, frameon=True, title="Version")
        fig.suptitle(f"{dataset}: Optimized query runtime (log scale)", y=1.02)
        plt.tight_layout()
        plt.savefig(OUT_ROOT / f"boxplot_{dataset}.pdf", dpi=150, bbox_inches="tight")
        plt.close()


def plot_speedup(speedup: pd.DataFrame) -> None:
    if speedup.empty:
        return

    for dataset in DATASETS:
        sub = speedup[speedup["dataset"] == dataset].copy()
        if sub.empty:
            continue

        sub["query_num"] = sub["query"].str[1:].astype(int)
        sub["variant"] = pd.Categorical(sub["variant"], categories=VARIANT_ORDER, ordered=True)
        sub = sub.sort_values(["query_num", "variant"])

        x = np.arange(len(sub))
        y = sub["speedup_old_over_new"].to_numpy()
        colors = ["#4c78a8" if v >= 1 else "#e45756" for v in y]

        fig, ax = plt.subplots(figsize=(14, 4.5))
        ax.bar(x, y, color=colors)
        ax.axhline(1.0, linestyle="--", color="black", linewidth=1)
        ax.set_yscale("log")
        ax.set_ylabel("Speedup old/new")
        ax.set_title(f"{dataset}: speedup old-case-study over case-study (median)")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{q}\n{v}" for q, v in zip(sub["query"], sub["variant"])], rotation=90, fontsize=7)
        plt.tight_layout()
        plt.savefig(OUT_ROOT / f"speedup_{dataset}.pdf", dpi=150, bbox_inches="tight")
        plt.close()


def print_overall_summary(speedup: pd.DataFrame) -> None:
    if speedup.empty:
        print("No speedup data available.")
        return

    print("\n=== Overall summary (median speedup old/new) ===")
    for dataset in DATASETS:
        sub = speedup[speedup["dataset"] == dataset]["speedup_old_over_new"].dropna()
        if sub.empty:
            continue

        gmean = float(np.exp(np.mean(np.log(sub))))
        print(f"{dataset:8s} | points={len(sub):3d} | gmean={gmean:8.3f}x | median={sub.median():8.3f}x | min={sub.min():8.3f}x | max={sub.max():8.3f}x")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare case-study vs old-case-study for selected datasets.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DATASETS,
        choices=DATASETS,
        help="Datasets to compare",
    )
    args = parser.parse_args()

    selected = args.datasets
    all_rows: list[dict] = []
    for ds in selected:
        all_rows.extend(collect_rows(ds, CASE_ROOT, "case-study"))
        all_rows.extend(collect_rows(ds, OLD_ROOT, "old-case-study"))

    if not all_rows:
        print("No benchmark rows were found. Please check the evaluation directories.")
        return

    df = pd.DataFrame(all_rows)
    summary = summarize(df)
    speedup = build_speedup(summary)

    save_tables(summary, speedup)
    plot_dataset_boxplots(df)
    plot_speedup(speedup)

    print("Rows loaded:", len(df))
    print("Summary rows:", len(summary))
    print("Output directory:", OUT_ROOT)
    print_overall_summary(speedup)


if __name__ == "__main__":
    main()
