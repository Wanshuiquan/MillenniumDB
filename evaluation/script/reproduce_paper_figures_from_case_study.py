#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from scipy.stats import gmean, pearsonr
except Exception:
    pearsonr = None
    gmean = None


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


def list_memory_leaves() -> list[Leaf]:
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
                    if leaf.exists() and (leaf / "memory.json").exists():
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
                "total_memory_mb": solver_mem_mb,
                "oracle_query_count": oracle_count,
            }
        )

    return rows


def parse_memory_json(path: Path, query_template: int) -> list[float]:
    if not path.exists():
        return []

    key = f"q{query_template}"
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return []

    values = payload.get(key, []) if isinstance(payload, dict) else []
    if not isinstance(values, list):
        return []

    parsed: list[float] = []
    for v in values:
        try:
            parsed.append(float(v))
        except (TypeError, ValueError):
            parsed.append(np.nan)
    return parsed


def build_exec_df(leaves: list[Leaf]) -> pd.DataFrame:
    rows: list[dict] = []
    for leaf in leaves:
        exec_rows = parse_db_log(leaf.path / "db.log")
        memory_values = parse_memory_json(leaf.path / "memory.json", leaf.query_template)

        for rec in exec_rows:
            idx = rec.get("exec_idx", -1)
            if isinstance(idx, int) and 0 <= idx < len(memory_values):
                rec["total_memory_mb"] = memory_values[idx]

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
        "total_memory_mb",
        "oracle_query_count",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["dataset"] = pd.Categorical(df["dataset"], categories=DATASET_ORDER, ordered=True)
    df["algorithm"] = pd.Categorical(df["algorithm"], categories=ALGO_ORDER, ordered=True)
    return df


def build_memory_df(leaves: list[Leaf]) -> pd.DataFrame:
    rows: list[dict] = []
    for leaf in leaves:
        memory_values = parse_memory_json(leaf.path / "memory.json", leaf.query_template)
        for idx, mem in enumerate(memory_values):
            rows.append(
                {
                    "exec_idx": idx,
                    "dataset_key": leaf.dataset_key,
                    "dataset": leaf.dataset_code,
                    "algorithm": leaf.algorithm,
                    "query_template": leaf.query_template,
                    "regular_category": REGULAR_CATEGORY.get(leaf.query_template, "rarely_used"),
                    "variant": leaf.variant,
                    "data_complexity": parse_data_complexity(leaf.variant),
                    "query_family": query_family(leaf.variant),
                    "total_memory_mb": mem,
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No memory rows parsed from evaluation/case-study memory.json.")

    df["total_memory_mb"] = pd.to_numeric(df["total_memory_mb"], errors="coerce")
    df["dataset"] = pd.Categorical(df["dataset"], categories=DATASET_ORDER, ordered=True)
    df["algorithm"] = pd.Categorical(df["algorithm"], categories=ALGO_ORDER, ordered=True)
    return df


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, format="pdf", bbox_inches="tight", dpi=220)
    plt.close()


def style_axis(ax: plt.Axes, x_label: str, y_label: str, y_log: bool = False, fontsize: int = 12) -> None:
    if y_log:
        ax.set_yscale("log")
    ax.set_xlabel(x_label, fontsize=fontsize)
    ax.set_ylabel(y_label, fontsize=fontsize)
    ax.tick_params(axis="x", labelsize=fontsize)
    ax.tick_params(axis="y", labelsize=fontsize)
    ax.grid(True, axis="y", alpha=0.3)


def place_legend_outside(ax: plt.Axes, ncol: int = 2, y: float = 1.18, fontsize: int = 12) -> None:
    leg = ax.get_legend()
    if leg is not None:
        leg.remove()
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(
            handles, labels, loc="upper center", bbox_to_anchor=(0.5, y), ncol=ncol, frameon=True, fontsize=fontsize
        )


def fig5_runtime_data_constraints(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna()) & (~df["timed_out"])].copy()
    sub["data_complexity"] = pd.Categorical(sub["data_complexity"], categories=DATA_COMPLEXITY_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(16, 12))
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
    style_axis(ax, "Dataset", "Time (ms)", y_log=True, fontsize=45)
    place_legend_outside(ax, ncol=2, y=1.2, fontsize=45)
    # ax.set_title("Figure 5: Runtime Across Datasets and Data Constraints")
    savefig(OUT_ROOT / "figures" / "runtime_data_constraints.pdf")


def fig6_runtime_regular_templates(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (df["data_complexity"].notna()) & (~df["timed_out"])].copy()
    label_map = {
        "frequently_used": "Frequently-used",
        "occasionally_used": "Occasionally-used",
        "rarely_used": "Rarely-used",
    }
    sub["regular_label"] = sub["regular_category"].map(label_map)
    sub["regular_label"] = pd.Categorical(sub["regular_label"], categories=REGULAR_LABEL_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(24, 16))
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
    style_axis(ax, "Dataset", "Runtime (ms)", y_log=True, fontsize=45)
    place_legend_outside(ax, ncol=3, y=1.2, fontsize=45)
    # ax.set_title("Figure 6: Runtime Across Datasets and Regular Templates")
    savefig(OUT_ROOT / "figures" / "runtime_regular_templates.pdf")


def fig7_rpq_vs_prpq(df: pd.DataFrame) -> None:
    sub = df[(df["algorithm"] == "optimized") & (~df["timed_out"])].copy()
    sub["query_family"] = pd.Categorical(sub["query_family"], categories=QUERY_FAMILY_ORDER, ordered=True)
    _, ax = plt.subplots(figsize=(20, 16))
    sns.boxenplot(
        data=sub,
        x="dataset",
        y="total_ms",
        hue="query_family",
        hue_order=QUERY_FAMILY_ORDER,
        palette=PALETTE_BINARY,
        ax=ax,
        showfliers=False,
    )
    style_axis(ax, "Dataset", "Time (ms)", y_log=True, fontsize=45)
    place_legend_outside(ax, ncol=2, y=1.2, fontsize=45)
    # ax.set_title("Figure 7: Runtime of RPQ vs PRPQ Across Datasets")
    savefig(OUT_ROOT / "figures" / "rpq_vs_prpq_runtime.pdf")


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
    memory_df = df[(df["algorithm"] == "optimized") & (df["total_memory_mb"].notna())].copy()
    memory_df["query_family"] = pd.Categorical(memory_df["query_family"], categories=QUERY_FAMILY_ORDER, ordered=True)

    _, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=memory_df,
        x="dataset",
        y="total_memory_mb",
        hue="query_family",
        hue_order=QUERY_FAMILY_ORDER,
        palette=PALETTE_BINARY,
        ax=ax,
        showfliers=False,
    )

    style_axis(ax, "Dataset", "Total Memory Usage (MB)", y_log=False)
    place_legend_outside(ax, ncol=2, y=1.2)
    ax.set_title("Figure 11: Total Memory Consumption of RPQ vs PRPQ")
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


def fig_z3_times_data_constraints(df: pd.DataFrame) -> None:
    """Two box plots for the optimized algorithm:
    - Left:  Z3 solver solving time (z3_solver_ms) grouped by dataset, hue = Simple / Complex Data
    - Right: Z3 operation time (z3_operation_ms) grouped by dataset, hue = Simple / Complex Data
    Only PRPQ variants (data-1 … data-5) are included since no-data runs carry no Z3 metrics.
    """
    sub = df[
        (df["algorithm"] == "optimized")
        & (df["data_complexity"].notna())
        & (~df["timed_out"])
        & (df["z3_solver_ms"].notna() | df["z3_operation_ms"].notna())
    ].copy()
    sub["data_complexity"] = pd.Categorical(sub["data_complexity"], categories=DATA_COMPLEXITY_ORDER, ordered=True)

    fig, axes = plt.subplots(1, 2, figsize=(28, 12), sharey=False)

    # Left panel: Z3 solver solving time
    sns.boxplot(
        data=sub.dropna(subset=["z3_solver_ms"]),
        x="dataset",
        y="z3_solver_ms",
        hue="data_complexity",
        hue_order=DATA_COMPLEXITY_ORDER,
        order=DATASET_ORDER,
        palette=PALETTE_BINARY,
        ax=axes[0],
        showfliers=False,
    )
    style_axis(axes[0], "Dataset", "Z3 Solver Time (ms)", y_log=True, fontsize=32)
    axes[0].set_title("Simple vs Complex Data — Z3 Solver Time", fontsize=28)
    leg = axes[0].get_legend()
    if leg is not None:
        leg.remove()

    # Right panel: Z3 operation time
    sns.boxplot(
        data=sub.dropna(subset=["z3_operation_ms"]),
        x="dataset",
        y="z3_operation_ms",
        hue="data_complexity",
        hue_order=DATA_COMPLEXITY_ORDER,
        order=DATASET_ORDER,
        palette=PALETTE_BINARY,
        ax=axes[1],
        showfliers=False,
    )
    style_axis(axes[1], "Dataset", "Z3 Operation Time (ms)", y_log=True, fontsize=32)
    axes[1].set_title("Simple vs Complex Data — Z3 Operation Time", fontsize=28)
    leg = axes[1].get_legend()
    if leg is not None:
        leg.remove()

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=True, fontsize=32)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(OUT_ROOT / "figures" / "z3_times_data_constraints.pdf")


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


def compute_geometric_average(df: pd.DataFrame, algorithm: str, query_family: str) -> float:
    """
    Compute the geometric average of memory consumption for a specific algorithm and query family.

    Parameters:
        df (pd.DataFrame): The dataframe containing execution data.
        algorithm (str): The algorithm to filter (e.g., "optimized").
        query_family (str): The query family to filter (e.g., "RPQ").

    Returns:
        float: The geometric average of memory consumption.
    """
    # Enforce family-to-variant mapping: RPQ -> no-data, PRPQ -> with-data constraints.
    if query_family == "RPQ":
        filtered_df = df[(df["algorithm"] == algorithm) & (df["variant"] == "no-data")]
    elif query_family == "PRPQ":
        filtered_df = df[(df["algorithm"] == algorithm) & (df["variant"] != "no-data")]
    else:
        raise ValueError(f"Unknown query_family: {query_family}")

    # Extract memory consumption values and remove NaN values
    memory_values = filtered_df["total_memory_mb"].dropna()
    memory_values = memory_values[memory_values > 0]

    # Compute the geometric average
    if len(memory_values) == 0:
        raise ValueError("No memory consumption data available for the specified filters.")

    geometric_average = np.exp(np.mean(np.log(memory_values)))
    return geometric_average


def compute_geometric_average_by_constraint(df: pd.DataFrame, algorithm: str, query_family: str) -> dict:
    """
    Compute the geometric average of memory consumption classified by "no-data" and "has data constraints".

    Parameters:
        df (pd.DataFrame): The dataframe containing execution data.
        algorithm (str): The algorithm to filter (e.g., "optimized").
        query_family (str): The query family to filter (e.g., "RPQ").

    Returns:
        dict: A dictionary with geometric averages for "no-data" and "has data constraints".
    """
    # Enforce family-to-variant mapping: RPQ -> no-data, PRPQ -> with-data constraints.
    if query_family == "RPQ":
        filtered_df = df[(df["algorithm"] == algorithm) & (df["variant"] == "no-data")]
    elif query_family == "PRPQ":
        filtered_df = df[(df["algorithm"] == algorithm) & (df["variant"] != "no-data")]
    else:
        raise ValueError(f"Unknown query_family: {query_family}")

    # Separate into "no-data" and "has data constraints"
    no_data_df = filtered_df[filtered_df["variant"] == "no-data"]
    has_data_df = filtered_df[filtered_df["variant"] != "no-data"]

    # Compute geometric averages
    results = {}

    for label, subset in {"no-data": no_data_df, "has data constraints": has_data_df}.items():
        memory_values = subset["total_memory_mb"].dropna()
        memory_values = memory_values[memory_values > 0]
        if len(memory_values) == 0:
            results[label] = None  # No data available for this category
        else:
            results[label] = np.exp(np.mean(np.log(memory_values)))

    return results


def export_memory_geometric_average_by_dataset(df: pd.DataFrame) -> None:
    """
    Export geometric averages of memory by dataset column and query family.

    Rule:
    - RPQ uses only variant == "no-data"
    - PRPQ uses only variant != "no-data"
    """
    sub = df[df["total_memory_mb"].notna()].copy()
    sub = sub[sub["total_memory_mb"] > 0]
    sub["query_family"] = np.where(sub["variant"] == "no-data", "RPQ", "PRPQ")

    grouped = (
        sub.groupby(["algorithm", "dataset", "query_family"], as_index=False)["total_memory_mb"]
        .apply(lambda s: float(np.exp(np.mean(np.log(s)))))
        .rename(columns={"total_memory_mb": "geometric_avg_memory_mb"})
    )

    grouped["algorithm"] = pd.Categorical(grouped["algorithm"], categories=ALGO_ORDER, ordered=True)
    grouped["dataset"] = pd.Categorical(grouped["dataset"], categories=DATASET_ORDER, ordered=True)
    grouped["query_family"] = pd.Categorical(grouped["query_family"], categories=QUERY_FAMILY_ORDER, ordered=True)
    grouped = grouped.sort_values(["algorithm", "dataset", "query_family"])

    grouped.to_csv(OUT_ROOT / "tables" / "memory_geometric_avg_by_dataset_query_family.csv", index=False)

    pivot = grouped.pivot(index=["algorithm", "query_family"], columns="dataset", values="geometric_avg_memory_mb")
    pivot = pivot.reindex(
        index=pd.MultiIndex.from_product([ALGO_ORDER, QUERY_FAMILY_ORDER], names=["algorithm", "query_family"]),
        columns=DATASET_ORDER,
    )
    pivot.to_csv(OUT_ROOT / "tables" / "memory_geometric_avg_pivot_rpq_prpq_by_dataset.csv")

    print("=== Geometric Average Memory (MB) by Dataset Column, Algorithm, and Query Family ===")
    print(grouped.to_string(index=False))
    print()


def export_solver_memory_validation(exec_df: pd.DataFrame, memory_df: pd.DataFrame) -> None:
    """
    Validate (using arithmetic averages):
      avg_memory_rpq + avg_solver_memory_prpq ?= avg_memory_prpq

    - avg_memory_* is computed from memory.json-derived rows.
    - avg_solver_memory_prpq is computed from db.log solver_memory_consumption on data-* variants.
    """
    mem = memory_df[memory_df["total_memory_mb"].notna()].copy()
    mem = mem[mem["total_memory_mb"] > 0]
    mem["query_family"] = np.where(mem["variant"] == "no-data", "RPQ", "PRPQ")

    mem_avg = mem.groupby(["algorithm", "dataset", "query_family"], as_index=False, observed=True).agg(
        avg_memory_mb=("total_memory_mb", "mean")
    )

    rpq = mem_avg[mem_avg["query_family"] == "RPQ"][["algorithm", "dataset", "avg_memory_mb"]].rename(
        columns={"avg_memory_mb": "avg_memory_rpq_mb"}
    )
    prpq = mem_avg[mem_avg["query_family"] == "PRPQ"][["algorithm", "dataset", "avg_memory_mb"]].rename(
        columns={"avg_memory_mb": "avg_memory_prpq_mb"}
    )

    solver = exec_df[(exec_df["variant"] != "no-data") & (exec_df["solver_memory_mb"].notna())].copy()
    solver = solver[solver["solver_memory_mb"] > 0]
    solver_avg = solver.groupby(["algorithm", "dataset"], as_index=False, observed=True).agg(
        avg_solver_memory_prpq_mb=("solver_memory_mb", "mean")
    )

    validation = rpq.merge(prpq, on=["algorithm", "dataset"], how="outer")
    validation = validation.merge(solver_avg, on=["algorithm", "dataset"], how="left")

    validation["lhs_rpq_plus_solver_mb"] = validation["avg_memory_rpq_mb"] + validation["avg_solver_memory_prpq_mb"]
    validation["rhs_prpq_mb"] = validation["avg_memory_prpq_mb"]
    validation["delta_mb"] = validation["lhs_rpq_plus_solver_mb"] - validation["rhs_prpq_mb"]
    validation["relative_delta_pct"] = np.where(
        validation["rhs_prpq_mb"] > 0,
        100.0 * validation["delta_mb"] / validation["rhs_prpq_mb"],
        np.nan,
    )

    # A practical equality check under noise: |delta| <= 5% of PRPQ average.
    validation["approx_equal_5pct"] = np.where(
        validation["rhs_prpq_mb"] > 0,
        np.abs(validation["delta_mb"]) <= 0.05 * validation["rhs_prpq_mb"],
        False,
    )

    validation["algorithm"] = pd.Categorical(validation["algorithm"], categories=ALGO_ORDER, ordered=True)
    validation["dataset"] = pd.Categorical(validation["dataset"], categories=DATASET_ORDER, ordered=True)
    validation = validation.sort_values(["algorithm", "dataset"])

    validation.to_csv(OUT_ROOT / "tables" / "memory_solver_validation_rpq_plus_solver_equals_prpq.csv", index=False)

    print("=== Validation: avg_memory_rpq + avg_solver_memory_prpq ?= avg_memory_prpq ===")
    print(
        validation[
            [
                "algorithm",
                "dataset",
                "avg_memory_rpq_mb",
                "avg_solver_memory_prpq_mb",
                "avg_memory_prpq_mb",
                "delta_mb",
                "relative_delta_pct",
                "approx_equal_5pct",
            ]
        ].to_string(index=False)
    )
    print()


def export_pairwise_solver_memory_validation(leaves: list[Leaf]) -> None:
    """
    Pairwise validation at execution index i for each data-* leaf:
      memory_no_data[i] + solver_memory_data[i] ?= memory_data[i]

    Matching key for no-data counterpart:
      (dataset_key, algorithm, query_template)
    """
    leaf_map = {(leaf.dataset_key, leaf.algorithm, leaf.query_template, leaf.variant): leaf for leaf in leaves}

    pair_rows: list[dict] = []
    for leaf in leaves:
        if not leaf.variant.startswith("data-"):
            continue

        no_data_leaf = leaf_map.get((leaf.dataset_key, leaf.algorithm, leaf.query_template, "no-data"))
        if no_data_leaf is None:
            continue

        mem_no_data = parse_memory_json(no_data_leaf.path / "memory.json", no_data_leaf.query_template)
        mem_data = parse_memory_json(leaf.path / "memory.json", leaf.query_template)
        solver_data = [rec.get("solver_memory_mb", np.nan) for rec in parse_db_log(leaf.path / "db.log")]

        n = min(len(mem_no_data), len(mem_data), len(solver_data))
        for i in range(n):
            no_val = mem_no_data[i]
            solver_val = solver_data[i]
            data_val = mem_data[i]

            lhs = np.nan
            if not np.isnan(no_val) and not np.isnan(solver_val):
                lhs = no_val + solver_val

            delta = np.nan
            if not np.isnan(lhs) and not np.isnan(data_val):
                delta = lhs - data_val

            rel_pct = np.nan
            approx_equal_5pct = False
            if not np.isnan(delta) and data_val > 0:
                rel_pct = 100.0 * delta / data_val
                approx_equal_5pct = bool(abs(delta) <= 0.05 * data_val)

            pair_rows.append(
                {
                    "dataset": leaf.dataset_code,
                    "algorithm": leaf.algorithm,
                    "query_template": leaf.query_template,
                    "variant": leaf.variant,
                    "exec_idx": i,
                    "memory_no_data_mb": no_val,
                    "solver_memory_data_mb": solver_val,
                    "memory_data_mb": data_val,
                    "lhs_no_data_plus_solver_mb": lhs,
                    "rhs_data_mb": data_val,
                    "delta_mb": delta,
                    "relative_delta_pct": rel_pct,
                    "approx_equal_5pct": approx_equal_5pct,
                }
            )

    pair_df = pd.DataFrame(pair_rows)
    if pair_df.empty:
        print("No pairwise rows produced for solver-memory validation.")
        return

    pair_df["dataset"] = pd.Categorical(pair_df["dataset"], categories=DATASET_ORDER, ordered=True)
    pair_df["algorithm"] = pd.Categorical(pair_df["algorithm"], categories=ALGO_ORDER, ordered=True)
    pair_df = pair_df.sort_values(["algorithm", "dataset", "query_template", "variant", "exec_idx"])

    pair_df.to_csv(OUT_ROOT / "tables" / "pairwise_memory_solver_validation_rows.csv", index=False)

    # Correlation summary classified by data constraint per dataset (aggregated over algorithms).
    corr_rows: list[dict] = []
    for (dataset, variant), g in pair_df.groupby(["dataset", "variant"], observed=True):
        if not str(variant).startswith("data-"):
            continue

        h = g.dropna(subset=["lhs_no_data_plus_solver_mb", "rhs_data_mb"])
        n = len(h)
        if n < 3:
            corr_rows.append(
                {
                    "dataset": dataset,
                    "data_constraint": variant,
                    "n": n,
                    "pearson_corr": np.nan,
                    "p_value": np.nan,
                }
            )
            continue

        x = h["lhs_no_data_plus_solver_mb"].to_numpy(dtype=float)
        y = h["rhs_data_mb"].to_numpy(dtype=float)
        if np.nanstd(x) == 0 or np.nanstd(y) == 0:
            corr_rows.append(
                {
                    "dataset": dataset,
                    "data_constraint": variant,
                    "n": n,
                    "pearson_corr": np.nan,
                    "p_value": np.nan,
                }
            )
            continue

        if pearsonr is not None:
            r, p = pearsonr(x, y)
            p_value = float(p)
        else:
            r = float(np.corrcoef(x, y)[0, 1])
            p_value = np.nan

        corr_rows.append(
            {
                "dataset": dataset,
                "data_constraint": variant,
                "n": n,
                "pearson_corr": float(r),
                "p_value": p_value,
            }
        )

    corr_df = pd.DataFrame(corr_rows)
    if not corr_df.empty:
        corr_df["dataset"] = pd.Categorical(corr_df["dataset"], categories=DATASET_ORDER, ordered=True)
        corr_df = corr_df.sort_values(["dataset", "data_constraint"])
        corr_df.to_csv(
            OUT_ROOT / "tables" / "pairwise_memory_solver_correlation_by_dataset_constraint.csv", index=False
        )

        print("=== Pairwise Correlation by Dataset and Data Constraint (with p-value) ===")
        print(corr_df.to_string(index=False))
        print()

    summary = pair_df.groupby(["algorithm", "dataset", "variant"], as_index=False, observed=True).agg(
        matched_pairs=("delta_mb", "size"),
        mean_delta_mb=("delta_mb", "mean"),
        mean_abs_delta_mb=("delta_mb", lambda s: float(np.nanmean(np.abs(s.to_numpy(dtype=float))))),
        median_abs_delta_mb=("delta_mb", lambda s: float(np.nanmedian(np.abs(s.to_numpy(dtype=float))))),
        mean_relative_delta_pct=("relative_delta_pct", "mean"),
        approx_equal_5pct_rate=("approx_equal_5pct", "mean"),
    )
    summary["approx_equal_5pct_rate"] = summary["approx_equal_5pct_rate"] * 100.0
    summary["dataset"] = pd.Categorical(summary["dataset"], categories=DATASET_ORDER, ordered=True)
    summary["algorithm"] = pd.Categorical(summary["algorithm"], categories=ALGO_ORDER, ordered=True)
    summary = summary.sort_values(["algorithm", "dataset", "variant"])

    summary.to_csv(OUT_ROOT / "tables" / "pairwise_memory_solver_validation_summary.csv", index=False)

    print("=== Pairwise Validation: memory_no_data[i] + solver_data[i] ?= memory_data[i] ===")
    print(summary.to_string(index=False))
    print()


def export_execution_time_decomposition_validation(exec_df: pd.DataFrame, tolerance_ms: float = 5.0) -> None:
    """
    Validate, for each data-* execution row i, the identity:

      execution_ms(data, i) ?= execution_ms(no-data, i) + z3_operation_ms(data, i) + z3_solver_ms(data, i)

    Matching key for the no-data counterpart:
      (dataset_key, algorithm, query_template, exec_idx)
    """
    key_cols = ["dataset_key", "algorithm", "query_template", "exec_idx"]

    no_data = exec_df[exec_df["variant"] == "no-data"][key_cols + ["execution_ms"]].rename(
        columns={"execution_ms": "execution_ms_no_data"}
    )

    data_rows = exec_df[exec_df["variant"].astype(str).str.startswith("data-")][
        key_cols
        + [
            "dataset",
            "variant",
            "timed_out",
            "execution_ms",
            "z3_operation_ms",
            "z3_solver_ms",
        ]
    ].copy()

    merged = data_rows.merge(no_data, on=key_cols, how="left")
    merged["predicted_execution_ms"] = (
        merged["execution_ms_no_data"] + merged["z3_operation_ms"] + merged["z3_solver_ms"]
    )
    merged["delta_ms"] = merged["execution_ms"] - merged["predicted_execution_ms"]
    merged["abs_delta_ms"] = merged["delta_ms"].abs()
    merged["within_tolerance"] = merged["abs_delta_ms"] <= tolerance_ms

    valid = merged.dropna(
        subset=[
            "execution_ms",
            "execution_ms_no_data",
            "z3_operation_ms",
            "z3_solver_ms",
            "predicted_execution_ms",
            "delta_ms",
        ]
    ).copy()

    merged.to_csv(OUT_ROOT / "tables" / "execution_time_decomposition_validation_rows.csv", index=False)

    if valid.empty:
        print("No comparable rows produced for execution-time decomposition validation.")
        return

    summary = pd.DataFrame(
        [
            {
                "rows_compared": int(len(valid)),
                "mean_delta_ms": float(valid["delta_ms"].mean()),
                "median_delta_ms": float(valid["delta_ms"].median()),
                "mean_abs_delta_ms": float(valid["abs_delta_ms"].mean()),
                "median_abs_delta_ms": float(valid["abs_delta_ms"].median()),
                "p95_abs_delta_ms": float(valid["abs_delta_ms"].quantile(0.95)),
                "within_tolerance_count": int(valid["within_tolerance"].sum()),
                "within_tolerance_rate_pct": float(valid["within_tolerance"].mean() * 100.0),
                "tolerance_ms": float(tolerance_ms),
            }
        ]
    )
    summary.to_csv(OUT_ROOT / "tables" / "execution_time_decomposition_validation_summary.csv", index=False)

    by_variant = valid.groupby("variant", as_index=False, observed=True).agg(
        n=("delta_ms", "size"),
        mean_delta_ms=("delta_ms", "mean"),
        mean_abs_delta_ms=("abs_delta_ms", "mean"),
        median_abs_delta_ms=("abs_delta_ms", "median"),
        p95_abs_delta_ms=("abs_delta_ms", lambda s: float(s.quantile(0.95))),
        within_tolerance_rate_pct=("within_tolerance", lambda s: float(s.mean() * 100.0)),
    )
    by_variant = by_variant.sort_values("variant")
    by_variant.to_csv(OUT_ROOT / "tables" / "execution_time_decomposition_by_variant.csv", index=False)

    by_dataset = valid.groupby("dataset", as_index=False, observed=True).agg(
        n=("delta_ms", "size"),
        mean_delta_ms=("delta_ms", "mean"),
        mean_abs_delta_ms=("abs_delta_ms", "mean"),
        median_abs_delta_ms=("abs_delta_ms", "median"),
        p95_abs_delta_ms=("abs_delta_ms", lambda s: float(s.quantile(0.95))),
        within_tolerance_rate_pct=("within_tolerance", lambda s: float(s.mean() * 100.0)),
    )
    by_dataset["dataset"] = pd.Categorical(by_dataset["dataset"], categories=DATASET_ORDER, ordered=True)
    by_dataset = by_dataset.sort_values("dataset")
    by_dataset.to_csv(OUT_ROOT / "tables" / "execution_time_decomposition_by_dataset.csv", index=False)

    print("=== Execution-Time Decomposition Validation ===")
    print(
        f"Compared rows: {int(summary.loc[0, 'rows_compared'])}, "
        f"mean abs delta: {summary.loc[0, 'mean_abs_delta_ms']:.6f} ms, "
        f"median abs delta: {summary.loc[0, 'median_abs_delta_ms']:.6f} ms, "
        f"p95 abs delta: {summary.loc[0, 'p95_abs_delta_ms']:.6f} ms, "
        f"within {tolerance_ms:.3f} ms: {summary.loc[0, 'within_tolerance_rate_pct']:.2f}%"
    )
    print()


# Example usage (uncomment to use after building the dataframe):
# df = build_exec_df(list_leaves())
# geo_avg = compute_geometric_average(df, "optimized", "RPQ")
# print(f"Geometric Average of Memory Consumption: {geo_avg:.2f} MB")
# geo_avg_by_constraint = compute_geometric_average_by_constraint(df, "optimized", "RPQ")
# print("Geometric Averages:", geo_avg_by_constraint)


def export_no_data_results_with_geometric_avg(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Export the no-data results with geometric averages to a CSV file.

    Parameters:
        df (pd.DataFrame): The dataframe containing execution data.
        output_dir (Path): The directory where the CSV file will be saved.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter for no-data results
    no_data_df = df[df["variant"] == "no-data"]

    # Compute geometric averages grouped by dataset and algorithm
    grouped = no_data_df.groupby(["dataset", "algorithm"])
    results = grouped["total_memory_mb"].apply(
        lambda x: np.exp(np.mean(np.log(x.dropna()))) if len(x.dropna()) > 0 else None
    )

    # Convert to a DataFrame
    results_df = results.reset_index(name="geometric_avg_memory_mb")

    # Save to CSV
    output_path = output_dir / "no_data_results_with_geometric_avg.csv"
    results_df.to_csv(output_path, index=False)
    print(f"Exported no-data results with geometric averages to {output_path}")


# Example usage (uncomment to use after building the dataframe):
# df = build_exec_df(list_leaves())
# export_no_data_results_with_geometric_avg(df, Path("/home/heyang-li/research/MillenniumDB/evaluation/exports"))


def main() -> None:
    ensure_dirs()
    sns.set_theme(style="whitegrid", context="talk")

    leaves = list_leaves()
    exec_df = build_exec_df(leaves)
    memory_df = build_memory_df(list_memory_leaves())

    exec_df.to_csv(OUT_ROOT / "tables" / "execution_rows.csv", index=False)
    export_runtime_stats_tables(exec_df)
    export_execution_time_decomposition_validation(exec_df)
    export_memory_geometric_average_by_dataset(memory_df)
    export_solver_memory_validation(exec_df, memory_df)
    export_pairwise_solver_memory_validation(leaves)

    fig5_runtime_data_constraints(exec_df)
    fig6_runtime_regular_templates(exec_df)
    fig7_rpq_vs_prpq(exec_df)
    fig8_runtime_vs_oracle(exec_df)
    fig9_oracle_data_constraints(exec_df)
    fig10_oracle_regular_templates(exec_df)
    fig11_memory_rpq_vs_prpq(memory_df)
    fig12_runtime_naive_vs_opt(exec_df)
    fig13_timeout_rate(exec_df)
    fig_z3_times_data_constraints(exec_df)

    manifest = sorted(str(p.relative_to(ROOT)) for p in (OUT_ROOT / "figures").glob("*.pdf"))
    pd.DataFrame({"pdf": manifest}).to_csv(OUT_ROOT / "tables" / "figure_manifest.csv", index=False)

    print(f"Parsed rows: {len(exec_df):,}")
    print(f"Output directory: {OUT_ROOT}")
    print(f"Generated figures: {len(manifest)}")


if __name__ == "__main__":
    main()
