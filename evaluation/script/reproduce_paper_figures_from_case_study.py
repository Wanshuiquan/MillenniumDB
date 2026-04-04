#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from scipy.stats import pearsonr
except Exception:
    pearsonr = None


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "case-study"
OUT_ROOT = ROOT / "figure" / "paper-reproduced-new-format"

DATASET_ORDER = ["L1", "L0", "PO", "TE", "IL", "IP"]
DATASET_CODE = {
    "ldbc10": "L1",
    "ldbc01": "L0",
    "pokec": "PO",
    "telecom": "TE",
    "icij-leak": "IL",
    "paradise": "IP",
}

ALGO_ORDER = ["optimized", "naive"]
VARIANT_ORDER = ["data-1", "data-2", "data-3", "data-4", "data-5", "no-data"]
DATA_COMPLEXITY_ORDER = ["Simple Data", "Complex Data"]
REGULAR_LABEL_ORDER = ["Frequently-used", "Occasionally-used", "Rarely-used"]
QUERY_FAMILY_ORDER = ["RPQ", "PRPQ"]

PALETTE_BINARY = ["white", "grey"]
PALETTE_TERNARY = ["white", "lightgrey", "darkgrey"]
PALETTE_ALGO = ["white", "grey"]

REGULAR_CATEGORY = {
    # Paper categories (same grouping used in legacy scripts)
    1: "frequently_used",
    2: "frequently_used",
    3: "frequently_used",
    4: "frequently_used",
    5: "occasionally_used",
    6: "occasionally_used",
    7: "occasionally_used",
    8: "rarely_used",
    9: "rarely_used",
    10: "rarely_used",
    11: "rarely_used",
    12: "rarely_used",
}

FLOAT_RE = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


@dataclass
class Leaf:
    dataset_key: str
    dataset_code: str
    algorithm: str
    query_template: int
    variant: str
    path: Path


def ensure_dirs() -> None:
    for sub in ["figures", "tables"]:
        (OUT_ROOT / sub).mkdir(parents=True, exist_ok=True)


def parse_data_complexity(variant: str) -> str | None:
    if variant in {"data-1", "data-2"}:
        return "Simple Data"
    if variant in {"data-3", "data-4", "data-5"}:
        return "Complex Data"
    return None


def query_family(variant: str) -> str:
    return "RPQ" if variant == "no-data" else "PRPQ"


def list_leaves() -> list[Leaf]:
    leaves: list[Leaf] = []
    for ds_key, ds_code in DATASET_CODE.items():
        for algo in ALGO_ORDER:
            algo_dir = CASE_ROOT / ds_key / algo
            if not algo_dir.exists():
                continue
            q_dirs = sorted(
                [p for p in algo_dir.iterdir() if p.is_dir() and p.name.startswith("Q")],
                key=lambda p: int(p.name[1:]),
            )
            for q in q_dirs:
                qnum = int(q.name[1:]) + 1
                for var in VARIANT_ORDER:
                    leaf = q / var
                    if leaf.exists() and (leaf / "db.log").exists():
                        leaves.append(
                            Leaf(
                                dataset_key=ds_key,
                                dataset_code=ds_code,
                                algorithm=algo,
                                query_template=qnum,
                                variant=var,
                                path=leaf,
                            )
                        )
    return leaves


def parse_db_log(path: Path) -> list[dict]:
    text = path.read_text(errors="ignore")
    chunks = re.findall(r"Query\(worker.*?(?=\nQuery\(worker|\Z)", text, flags=re.DOTALL)

    rows: list[dict] = []
    for idx, chunk in enumerate(chunks):
        parser_ms = np.nan
        optimizer_ms = np.nan
        execution_ms = np.nan
        timeout_ms = np.nan
        timed_out = False

        m = re.search(rf"Parser\s*:\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            parser_ms = float(m.group(1))
        m = re.search(rf"Optimizer\s*:\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            optimizer_ms = float(m.group(1))
        m = re.search(rf"Execution\s*:\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            execution_ms = float(m.group(1))

        m = re.search(rf"timed out after\s*({FLOAT_RE})\s*ms", chunk)
        if m:
            timeout_ms = float(m.group(1))
            timed_out = True

        m = re.search(r"results:\s*(\d+)", chunk)
        worker_results = int(m.group(1)) if m else np.nan

        m = re.search(rf"z3_operation_time\s*[:：]\s*({FLOAT_RE})\s*ms", chunk)
        z3_op_ms = float(m.group(1)) if m else np.nan

        m = re.search(rf"z3_solver_time\s*[:：]\s*({FLOAT_RE})\s*ms", chunk)
        z3_solver_ms = float(m.group(1)) if m else np.nan

        m = re.search(rf"solver_memory_consumption\s*[:：]\s*({FLOAT_RE})\s*MB", chunk)
        solver_mem_mb = float(m.group(1)) if m else np.nan

        m = re.search(rf"exploration_depth\s*[:：]\s*({FLOAT_RE})", chunk)
        oracle_count = float(m.group(1)) if m else np.nan

        total_ms = np.nan
        if not np.isnan(parser_ms) and not np.isnan(optimizer_ms) and not np.isnan(execution_ms):
            total_ms = parser_ms + optimizer_ms + execution_ms
        elif not np.isnan(timeout_ms):
            total_ms = timeout_ms

        rows.append(
            {
                "exec_idx": idx,
                "parser_ms": parser_ms,
                "optimizer_ms": optimizer_ms,
                "execution_ms": execution_ms,
                "timeout_ms": timeout_ms,
                "timed_out": timed_out,
                "total_ms": total_ms,
                "worker_results": worker_results,
                "z3_operation_ms": z3_op_ms,
                "z3_solver_ms": z3_solver_ms,
                "solver_memory_mb": solver_mem_mb,
                "oracle_query_count": oracle_count,
            }
        )

    return rows


def build_exec_df(leaves: list[Leaf]) -> pd.DataFrame:
    rows: list[dict] = []
    for leaf in leaves:
        for rec in parse_db_log(leaf.path / "db.log"):
            rec["dataset_key"] = leaf.dataset_key
            rec["dataset"] = leaf.dataset_code
            rec["algorithm"] = leaf.algorithm
            rec["query_template"] = leaf.query_template
            rec["regular_category"] = REGULAR_CATEGORY.get(leaf.query_template, "rarely_used")
            rec["variant"] = leaf.variant
            rec["data_complexity"] = parse_data_complexity(leaf.variant)
            rec["query_family"] = query_family(leaf.variant)
            rows.append(rec)

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No rows parsed from evaluation/case-study.")

    for c in [
        "parser_ms",
        "optimizer_ms",
        "execution_ms",
        "timeout_ms",
        "total_ms",
        "worker_results",
        "z3_operation_ms",
        "z3_solver_ms",
        "solver_memory_mb",
        "oracle_query_count",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["dataset"] = pd.Categorical(df["dataset"], categories=DATASET_ORDER, ordered=True)
    df["algorithm"] = pd.Categorical(df["algorithm"], categories=ALGO_ORDER, ordered=True)
    return df


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, format="pdf", bbox_inches="tight", dpi=220)
    plt.close()


def style_axis(ax: plt.Axes, x_label: str, y_label: str, y_log: bool = False) -> None:
    if y_log:
        ax.set_yscale("log")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, axis="y", alpha=0.3)


def place_legend_outside(ax: plt.Axes, ncol: int = 2, y: float = 1.18) -> None:
    leg = ax.get_legend()
    if leg is not None:
        leg.remove()
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, y), ncol=ncol, frameon=True)


def fig5_runtime_data_constraints(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna()) & (~df["timed_out"])].copy()
    sub["data_complexity"] = pd.Categorical(sub["data_complexity"], categories=DATA_COMPLEXITY_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxenplot(
        data=sub,
        x="dataset",
        y="total_ms",
        hue="data_complexity",
        hue_order=DATA_COMPLEXITY_ORDER,
        palette=PALETTE_BINARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Time (ms)", y_log=True)
    place_legend_outside(ax, ncol=2, y=1.2)
    # ax.set_title("Figure 5: Runtime Across Datasets and Data Constraints")
    savefig(OUT_ROOT / "figures" / "figure5_runtime_data_constraints.pdf")


def fig6_runtime_regular_templates(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna()) & (~df["timed_out"])].copy()
    label_map = {
        "frequently_used": "Frequently-used",
        "occasionally_used": "Occasionally-used",
        "rarely_used": "Rarely-used",
    }
    sub["regular_label"] = sub["regular_category"].map(label_map)
    sub["regular_label"] = pd.Categorical(sub["regular_label"], categories=REGULAR_LABEL_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxenplot(
        data=sub,
        x="dataset",
        y="total_ms",
        hue="regular_label",
        hue_order=REGULAR_LABEL_ORDER,
        palette=PALETTE_TERNARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Runtime (ms)", y_log=True)
    place_legend_outside(ax, ncol=3, y=1.2)
    # ax.set_title("Figure 6: Runtime Across Datasets and Regular Templates")
    savefig(OUT_ROOT / "figures" / "figure6_runtime_regular_templates.pdf")


def fig7_rpq_vs_prpq(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (~df["timed_out"])].copy()
    sub["query_family"] = pd.Categorical(sub["query_family"], categories=QUERY_FAMILY_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=sub,
        x="dataset",
        y="total_ms",
        hue="query_family",
        hue_order=QUERY_FAMILY_ORDER,
        palette=PALETTE_BINARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Time (ms)", y_log=True)
    place_legend_outside(ax, ncol=2, y=1.2)
    ax.set_title("Figure 7: Runtime of RPQ vs PRPQ Across Datasets")
    savefig(OUT_ROOT / "figures" / "figure7_rpq_vs_prpq_runtime.pdf")


def fig8_runtime_vs_oracle(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna()) & (~df["timed_out"])].copy()
    sub = sub.dropna(subset=["oracle_query_count", "total_ms"])
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=False, sharey=False)

    # Left panel: individual runs
    sns.scatterplot(data=sub, x="oracle_query_count", y="total_ms", s=9, alpha=0.2, ax=axes[0], linewidth=0)
    style_axis(axes[0], "Oracle Query Counts", "Time (ms)", y_log=True)
    axes[0].set_xscale("log")
    axes[0].set_title("Individual Run")

    if len(sub) >= 2:
        x = sub["oracle_query_count"].to_numpy(dtype=float)
        y = sub["total_ms"].to_numpy(dtype=float)
        m, b = np.polyfit(x, y, 1)
        xs = np.linspace(np.nanmin(x), np.nanmax(x), 200)
        axes[1].scatter(x, y, s=9, alpha=0.12, color="black")
        axes[1].plot(xs, m * xs + b, color="red", linewidth=2)
        if pearsonr is not None:
            r, p = pearsonr(x, y)
            axes[1].text(
                0.02,
                0.98,
                f"r: {r:.3f}\np < 0.001" if p < 1e-3 else f"r: {r:.3f}\np = {p:.3g}",
                transform=axes[1].transAxes,
                va="top",
            )

    style_axis(axes[1], "Oracle Query Counts", "Runtime (ms)", y_log=True)
    axes[1].set_xscale("log")
    axes[1].set_title("Overall Trend")
    fig.suptitle("Figure 8: Runtime vs Oracle Query Count", y=1.02)
    savefig(OUT_ROOT / "figures" / "figure8_runtime_vs_oracle_query_count.pdf")


def fig9_oracle_data_constraints(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna())].copy()
    sub["data_complexity"] = pd.Categorical(sub["data_complexity"], categories=DATA_COMPLEXITY_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=sub,
        x="dataset",
        y="oracle_query_count",
        hue="data_complexity",
        hue_order=DATA_COMPLEXITY_ORDER,
        palette=PALETTE_BINARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Oracle Query Counts", y_log=True)
    place_legend_outside(ax, ncol=2, y=1.2)
    ax.set_title("Figure 9: Oracle Query Counts Across Data Constraints")
    savefig(OUT_ROOT / "figures" / "figure9_oracle_counts_data_constraints.pdf")


def fig10_oracle_regular_templates(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna())].copy()
    label_map = {
        "frequently_used": "Frequently-used",
        "occasionally_used": "Occasionally-used",
        "rarely_used": "Rarely-used",
    }
    sub["regular_label"] = sub["regular_category"].map(label_map)
    sub["regular_label"] = pd.Categorical(sub["regular_label"], categories=REGULAR_LABEL_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=sub,
        x="dataset",
        y="oracle_query_count",
        hue="regular_label",
        hue_order=REGULAR_LABEL_ORDER,
        palette=PALETTE_TERNARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Oracle Query Counts", y_log=True)
    place_legend_outside(ax, ncol=3, y=1.22)
    ax.set_title("Figure 10: Oracle Query Counts Across Regular Templates")
    savefig(OUT_ROOT / "figures" / "figure10_oracle_counts_regular_templates.pdf")


def fig11_memory_rpq_vs_prpq(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized")].copy()
    sub = sub.dropna(subset=["solver_memory_mb"])
    sub["query_family"] = pd.Categorical(sub["query_family"], categories=QUERY_FAMILY_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=sub,
        x="dataset",
        y="solver_memory_mb",
        hue="query_family",
        hue_order=QUERY_FAMILY_ORDER,
        palette=PALETTE_BINARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Memory Usage (MB)", y_log=True)
    place_legend_outside(ax, ncol=2, y=1.2)
    ax.set_title("Figure 11: Memory Consumption of RPQ vs PRPQ")
    savefig(OUT_ROOT / "figures" / "figure11_memory_rpq_vs_prpq.pdf")


def fig12_runtime_naive_vs_opt(df: pd.DataFrame) -> None:
    sub = df[(df["data_complexity"].notna()) & (~df["timed_out"])].copy()

    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=False, sharey=False)
    for i, ds in enumerate(DATASET_ORDER):
        ax = axes[i // 3, i % 3]
        dsub = sub[sub["dataset"] == ds]
        if dsub.empty:
            ax.set_visible(False)
            continue
        sns.boxplot(
            data=dsub,
            x="data_complexity",
            y="total_ms",
            hue="algorithm",
            hue_order=ALGO_ORDER,
            order=DATA_COMPLEXITY_ORDER,
            palette=PALETTE_ALGO,
            ax=ax,
            showfliers=False,
        )
        style_axis(ax, "", "Time (ms)", y_log=True)
        ax.set_title(ds)
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=2, frameon=True)
    fig.suptitle("Figure 12: Runtime Across Datasets and Data Constraints (Non-timeout)", y=1.02)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(OUT_ROOT / "figures" / "figure12_runtime_naive_vs_optimized.pdf")


def fig13_timeout_rate(df: pd.DataFrame) -> None:
    sub = df[df["data_complexity"].notna()].copy()
    timeout_rate = sub.groupby(["dataset", "data_complexity", "algorithm"], as_index=False).agg(
        timeout_rate=("timed_out", "mean"), n=("timed_out", "size")
    )
    timeout_rate = timeout_rate[timeout_rate["n"] > 0]
    timeout_rate["timeout_pct"] = timeout_rate["timeout_rate"] * 100.0

    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=False, sharey=False)
    for i, ds in enumerate(DATASET_ORDER):
        ax = axes[i // 3, i % 3]
        dsub = timeout_rate[timeout_rate["dataset"] == ds]
        if dsub.empty:
            ax.set_visible(False)
            continue
        sns.barplot(
            data=dsub,
            x="data_complexity",
            y="timeout_pct",
            hue="algorithm",
            order=DATA_COMPLEXITY_ORDER,
            palette=PALETTE_ALGO,
            ax=ax,
        )
        ax.set_title(ds)
        ax.set_xlabel("")
        ax.set_ylabel("Timeout Rate (%)")
        ymax = float(dsub["timeout_pct"].max()) if not dsub.empty else 100.0
        ax.set_ylim(0, min(100.0, max(10.0, ymax * 1.25)))
        ax.grid(True, axis="y", alpha=0.3)
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=2, frameon=True)
    fig.suptitle("Figure 13: Timeout Rate Across Datasets and Data Constraints", y=1.02)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(OUT_ROOT / "figures" / "figure13_timeout_rate_naive_vs_optimized.pdf")


def export_runtime_stats_tables(df: pd.DataFrame) -> None:
    sub = df[(df["data_complexity"].notna()) & (~df["timed_out"])].copy()

    # Overall table (all datasets pooled)
    avg_runtime = sub.groupby(["algorithm", "data_complexity"], as_index=False).agg(
        avg_ms=("total_ms", "mean"),
        median_ms=("total_ms", "median"),
        min_ms=("total_ms", "min"),
        max_ms=("total_ms", "max"),
        count=("total_ms", "size"),
    )
    avg_runtime = avg_runtime.sort_values(["data_complexity", "algorithm"])
    avg_runtime.to_csv(OUT_ROOT / "tables" / "avg_runtime_by_algorithm_complexity.csv", index=False)

    # Detailed combined table with dataset dimension
    dataset_runtime = sub.groupby(["dataset", "algorithm", "data_complexity"], as_index=False).agg(
        avg_ms=("total_ms", "mean"),
        median_ms=("total_ms", "median"),
        min_ms=("total_ms", "min"),
        max_ms=("total_ms", "max"),
        count=("total_ms", "size"),
    )
    dataset_runtime = dataset_runtime.sort_values(["dataset", "data_complexity", "algorithm"])
    dataset_runtime.to_csv(OUT_ROOT / "tables" / "runtime_stats_by_dataset_algorithm_complexity.csv", index=False)

    # One table per dataset
    for ds in DATASET_ORDER:
        ds_table = dataset_runtime[dataset_runtime["dataset"] == ds].copy()
        if ds_table.empty:
            continue
        ds_table.to_csv(OUT_ROOT / "tables" / f"runtime_stats_{ds}.csv", index=False)

    print("\n=== Average Runtime by Algorithm and Data Complexity (Non-timeout queries) ===")
    print(avg_runtime.to_string(index=False))
    print()
    print("=== Detailed Runtime Stats by Dataset / Algorithm / Data Complexity ===")
    print(dataset_runtime.to_string(index=False))
    print()


def main() -> None:
    ensure_dirs()
    sns.set_theme(style="whitegrid", context="talk")

    leaves = list_leaves()
    exec_df = build_exec_df(leaves)

    exec_df.to_csv(OUT_ROOT / "tables" / "execution_rows.csv", index=False)
    export_runtime_stats_tables(exec_df)

    fig5_runtime_data_constraints(exec_df)
    fig6_runtime_regular_templates(exec_df)
    fig7_rpq_vs_prpq(exec_df)
    fig8_runtime_vs_oracle(exec_df)
    fig9_oracle_data_constraints(exec_df)
    fig10_oracle_regular_templates(exec_df)
    fig11_memory_rpq_vs_prpq(exec_df)
    fig12_runtime_naive_vs_opt(exec_df)
    fig13_timeout_rate(exec_df)

    manifest = sorted(str(p.relative_to(ROOT)) for p in (OUT_ROOT / "figures").glob("*.pdf"))
    pd.DataFrame({"pdf": manifest}).to_csv(OUT_ROOT / "tables" / "figure_manifest.csv", index=False)

    print(f"Parsed rows: {len(exec_df):,}")
    print(f"Output directory: {OUT_ROOT}")
    print(f"Generated figures: {len(manifest)}")


if __name__ == "__main__":
    main()
