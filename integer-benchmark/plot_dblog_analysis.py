"""
Aggregate analysis from db.log files.

For each dataset, produce one figure with 2x2 subplots:
  rows = LIA, NIA
  cols = Optimized, Naive

Each subplot shows stacked boxplots of Parser / Optimizer / Execution times
grouped by query category (Frequent / Occasional / Rare), using a log-scale y-axis.

A second figure (one per dataset) shows Optimizer vs Execution time side-by-side
for optimized vs naive, to highlight the optimisation trade-off.

Output: results/figures/{dataset}_dblog_phases.png
        results/figures/{dataset}_dblog_opt_vs_exec.png
"""

from __future__ import annotations
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

LOGS_DIR = Path(__file__).parent / "logs"
RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

DATASETS = [
    ("ldbc01", "LDBC-01"),
    ("ldbc10", "LDBC-10"),
    ("pokec", "Pokec"),
    ("paradise", "Paradise"),
    ("telecom", "Telecom"),
    ("icij-leak", "ICIJ-Leak"),
]

CATEGORIES = ["Frequently-used", "Occasionally-used", "Rarely-used"]
CAT_SHORT = ["Frequent", "Occasional", "Rare"]

RE_PARSER = re.compile(r"^Parser\s*:\s*([\d.]+)\s*ms", re.MULTILINE)
RE_OPTIMIZER = re.compile(r"^Optimizer\s*:\s*([\d.]+)\s*ms", re.MULTILINE)
RE_EXECUTION = re.compile(r"^Execution\s*:\s*([\d.]+)\s*ms", re.MULTILINE)
RE_QUERY = re.compile(r"Query\(worker", re.MULTILINE)
RE_TIMEOUT = re.compile(r"timed out after ([\d.]+) ms", re.MULTILINE)


# Query template classification (same as trial CSV)
def template_category(template_idx: int) -> str:
    if 1 <= template_idx <= 4:
        return "Frequently-used"
    if 5 <= template_idx <= 7:
        return "Occasionally-used"
    if 8 <= template_idx <= 12:
        return "Rarely-used"
    return "Unknown"


def parse_log(log_path: Path) -> pd.DataFrame:
    """Parse a db.log and return a DataFrame with one row per query execution."""
    with open(log_path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Split into per-query blocks
    blocks = re.split(r"(?=Query\(worker)", text)
    rows = []
    for block in blocks:
        if "Query(" not in block:
            continue
        # Timing
        p = RE_PARSER.search(block)
        o = RE_OPTIMIZER.search(block)
        e = RE_EXECUTION.search(block)
        t = RE_TIMEOUT.search(block)

        if t:
            timeout_ms = float(t.group(1))
            rows.append(
                {
                    "parser_ms": None,
                    "optimizer_ms": None,
                    # Keep timeout duration in execution so boxplots include timeout samples.
                    "execution_ms": timeout_ms,
                    "total_ms": timeout_ms,
                    "timed_out": True,
                }
            )
        elif p and o and e:
            p_ms = float(p.group(1))
            o_ms = float(o.group(1))
            e_ms = float(e.group(1))
            rows.append(
                {
                    "parser_ms": p_ms,
                    "optimizer_ms": o_ms,
                    "execution_ms": e_ms,
                    "total_ms": p_ms + o_ms + e_ms,
                    "timed_out": False,
                }
            )
        # else: skip warmup / non-benchmark queries

    return pd.DataFrame(rows)


def load_all_logs(dataset: str) -> pd.DataFrame:
    """Load all four logs for a dataset into one DataFrame."""
    dfs = []
    for arith in ("lia", "nia"):
        for variant in ("optimized", "naive"):
            path = LOGS_DIR / dataset / arith / variant / "db.log"
            if not path.exists():
                print(f"  Missing: {path}")
                continue
            df = parse_log(path)
            df["arithmetic"] = arith.upper()
            df["variant"] = variant
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def load_trial_csv(dataset: str) -> pd.DataFrame | None:
    """Load the trial CSV to get per-query category labels."""
    # Try canonical name
    for stem in (f"{dataset}_lia_nia_trial", f"{dataset}_lra_trial"):
        p = RESULTS_DIR / f"{stem}.csv"
        if p.exists():
            return pd.read_csv(p)
    return None


# ─── Figure 1: phase breakdown boxplots ──────────────────────────────────────

PHASE_COLORS = {
    "parser_ms": "#4e79a7",
    "optimizer_ms": "#f28e2b",
    "execution_ms": "#59a14f",
}
PHASE_LABELS = {
    "parser_ms": "Parser",
    "optimizer_ms": "Optimizer",
    "execution_ms": "Execution",
}


def draw_phase_figure(df_log: pd.DataFrame, display_name: str, out_path: Path) -> None:
    """
    1×2 subplots (LIA, NIA). Each subplot shows side-by-side boxplots for
    Parser / Optimizer / Execution, comparing Optimized vs Naive.
    """
    arithmetics = ["LIA", "NIA"]
    phases = ["parser_ms", "optimizer_ms", "execution_ms"]

    positions_map = {
        ("parser_ms", "optimized"): 1,
        ("parser_ms", "naive"): 2,
        ("optimizer_ms", "optimized"): 4,
        ("optimizer_ms", "naive"): 5,
        ("execution_ms", "optimized"): 7,
        ("execution_ms", "naive"): 8,
    }
    colors_map = {
        ("parser_ms", "optimized"): "#4e79a7",
        ("parser_ms", "naive"): "#a8c8e8",
        ("optimizer_ms", "optimized"): "#f28e2b",
        ("optimizer_ms", "naive"): "#ffbe7d",
        ("execution_ms", "optimized"): "#59a14f",
        ("execution_ms", "naive"): "#b6d7a8",
    }
    tick_pos = [1.5, 4.5, 7.5]
    tick_labels = ["Parser", "Optimizer", "Execution"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)

    for col_i, arith in enumerate(arithmetics):
        ax = axes[col_i]
        sub = df_log[df_log["arithmetic"] == arith]
        for (phase, variant), pos in positions_map.items():
            vals = sub[sub["variant"] == variant][phase].dropna().tolist()
            color = colors_map[(phase, variant)]
            bp = ax.boxplot(
                [vals],
                positions=[pos],
                widths=0.60,
                patch_artist=True,
                showfliers=True,
                medianprops={"color": "black", "linewidth": 1.4},
                whiskerprops={"linewidth": 0.9},
                capprops={"linewidth": 0.9},
            )
            for box in bp["boxes"]:
                box.set(facecolor=color, alpha=0.80)

        for sep in [3, 6]:
            ax.axvline(sep, color="gray", linestyle=":", linewidth=0.9, alpha=0.6)

        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_labels, fontsize=11)
        ax.set_yscale("log")
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)
        ax.set_title(f"{arith}", fontsize=12)
        ax.set_ylabel("Time (ms, log scale)", fontsize=10)

    handles = []
    for phase, label in PHASE_LABELS.items():
        handles.append(mpatches.Patch(color=colors_map[(phase, "optimized")], alpha=0.80, label=f"{label} — optimized"))
        handles.append(mpatches.Patch(color=colors_map[(phase, "naive")], alpha=0.80, label=f"{label} — naive"))
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9, framealpha=0.85, bbox_to_anchor=(0.5, -0.04))

    fig.suptitle(
        f"{display_name}: Parser / Optimizer / Execution time — Optimized vs Naive\n"
        "(includes timeout samples in execution; log scale)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0.12, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


# ─── Figure 2: optimizer vs execution, optimized vs naive ────────────────────


def draw_opt_vs_exec_figure(df_log: pd.DataFrame, display_name: str, out_path: Path) -> None:
    """
    For each arithmetic (LIA/NIA), side-by-side boxplots:
      x-axis positions: Optimizer-optimized, Optimizer-naive, Execution-optimized, Execution-naive
    Shows how optimiser does more work to save execution time.
    """
    arithmetics = ["LIA", "NIA"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

    positions_map = {
        ("optimizer_ms", "optimized"): 1,
        ("optimizer_ms", "naive"): 2,
        ("execution_ms", "optimized"): 4,
        ("execution_ms", "naive"): 5,
    }
    colors_map = {
        ("optimizer_ms", "optimized"): "#f28e2b",
        ("optimizer_ms", "naive"): "#ffbe7d",
        ("execution_ms", "optimized"): "#59a14f",
        ("execution_ms", "naive"): "#b6d7a8",
    }
    tick_pos = [1.5, 4.5]
    tick_labels = ["Optimizer", "Execution"]

    for col_i, arith in enumerate(arithmetics):
        ax = axes[col_i]
        sub = df_log[df_log["arithmetic"] == arith]
        for (phase, variant), pos in positions_map.items():
            vals = sub[sub["variant"] == variant][phase].dropna().tolist()
            color = colors_map[(phase, variant)]
            bp = ax.boxplot(
                [vals],
                positions=[pos],
                widths=0.55,
                patch_artist=True,
                showfliers=True,
                medianprops={"color": "black", "linewidth": 1.4},
                whiskerprops={"linewidth": 0.9},
                capprops={"linewidth": 0.9},
            )
            for box in bp["boxes"]:
                box.set(facecolor=color, alpha=0.80)

        ax.axvline(3, color="gray", linestyle=":", linewidth=0.9, alpha=0.6)
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_labels, fontsize=11)
        ax.set_yscale("log")
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)
        ax.set_title(f"{arith}", fontsize=12)
        ax.set_ylabel("Time (ms, log scale)", fontsize=10)

    # Legend
    handles = [
        mpatches.Patch(color="#f28e2b", alpha=0.80, label="Optimizer — optimized"),
        mpatches.Patch(color="#ffbe7d", alpha=0.80, label="Optimizer — naive"),
        mpatches.Patch(color="#59a14f", alpha=0.80, label="Execution — optimized"),
        mpatches.Patch(color="#b6d7a8", alpha=0.80, label="Execution — naive"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=9, framealpha=0.85, bbox_to_anchor=(0.5, -0.04))

    fig.suptitle(
        f"{display_name}: Optimizer vs Execution time — Optimized vs Naive\n"
        "(includes timeout samples in execution; log scale)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


# ─── Figure 3: timeout rate per arithmetic/variant ───────────────────────────


def draw_timeout_figure_all(all_data: dict[str, pd.DataFrame], out_path: Path) -> None:
    """Bar chart: timeout rate (%) per dataset × arithmetic × variant."""
    records = []
    for dataset, df in all_data.items():
        for arith in ("LIA", "NIA"):
            for variant in ("optimized", "naive"):
                sub = df[(df["arithmetic"] == arith) & (df["variant"] == variant)]
                if sub.empty:
                    continue
                total = len(sub)
                n_to = sub["timed_out"].sum()
                records.append(
                    {
                        "dataset": dataset,
                        "arithmetic": arith,
                        "variant": variant,
                        "timeout_pct": 100 * n_to / total if total else 0,
                        "n_total": total,
                        "n_timeout": n_to,
                    }
                )
    df_t = pd.DataFrame(records)

    datasets = sorted(df_t["dataset"].unique())
    combos = [("LIA", "optimized"), ("LIA", "naive"), ("NIA", "optimized"), ("NIA", "naive")]
    combo_labels = ["LIA opt", "LIA naive", "NIA opt", "NIA naive"]
    combo_colors = ["#2E8B57", "#90EE90", "#c0392b", "#f1948a"]

    x = np.arange(len(datasets))
    n = len(combos)
    w = 0.18
    offsets = np.linspace(-(n - 1) * w / 2, (n - 1) * w / 2, n)

    fig, ax = plt.subplots(figsize=(12, 5))
    for i, ((arith, variant), label, color) in enumerate(zip(combos, combo_labels, combo_colors)):
        vals = []
        for ds in datasets:
            row = df_t[(df_t["dataset"] == ds) & (df_t["arithmetic"] == arith) & (df_t["variant"] == variant)]
            vals.append(float(row["timeout_pct"].values[0]) if not row.empty else 0.0)
        ax.bar(x + offsets[i], vals, width=w, label=label, color=color, alpha=0.85, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(datasets, fontsize=10)
    ax.set_ylabel("Timeout rate (%)", fontsize=11)
    ax.set_title("Query timeout rate by dataset, arithmetic, and variant", fontsize=12)
    ax.legend(fontsize=9, framealpha=0.85)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


# ─── Figure 4: runtime-only naive vs optimized (overwrite old naming) ───────


def draw_runtime_naive_vs_optimized(df_log: pd.DataFrame, display_name: str, out_path: Path) -> None:
    """
    Produce one figure per dataset with two subplots (LIA, NIA), where each subplot
    compares optimized vs naive using total running time from db.log.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), sharey=False)

    color_opt = "#2E8B57"
    color_naive = "#D2691E"

    for idx, arithmetic in enumerate(("LIA", "NIA")):
        ax = axes[idx]
        sub = df_log[df_log["arithmetic"] == arithmetic]
        opt_vals = sub[sub["variant"] == "optimized"]["total_ms"].dropna().tolist()
        naive_vals = sub[sub["variant"] == "naive"]["total_ms"].dropna().tolist()

        bp_opt = ax.boxplot(
            [opt_vals],
            positions=[1],
            widths=0.55,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.4},
            whiskerprops={"linewidth": 0.9},
            capprops={"linewidth": 0.9},
        )
        bp_naive = ax.boxplot(
            [naive_vals],
            positions=[2],
            widths=0.55,
            patch_artist=True,
            showfliers=True,
            medianprops={"color": "black", "linewidth": 1.4},
            whiskerprops={"linewidth": 0.9},
            capprops={"linewidth": 0.9},
        )

        for box in bp_opt["boxes"]:
            box.set(facecolor=color_opt, alpha=0.80)
        for box in bp_naive["boxes"]:
            box.set(facecolor=color_naive, alpha=0.80)

        ax.set_xticks([1, 2])
        ax.set_xticklabels(["Optimized", "Naive"], fontsize=10)
        ax.set_yscale("log")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.set_title(arithmetic, fontsize=12)
        ax.set_ylabel("Running time (ms, log scale)", fontsize=10)

    opt_handle = plt.Line2D([0], [0], color=color_opt, lw=8, alpha=0.80)
    naive_handle = plt.Line2D([0], [0], color=color_naive, lw=8, alpha=0.80)
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
        f"{display_name}: Naive vs Optimized — LIA & NIA\n" "(db.log-based running time; includes timeout samples)",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    all_data: dict[str, pd.DataFrame] = {}

    for dataset_key, display_name in DATASETS:
        print(f"\nProcessing {display_name}...")
        df = load_all_logs(dataset_key)
        if df.empty:
            print("  No data found, skipping.")
            continue
        all_data[dataset_key] = df

        completed = (~df["timed_out"]).sum()
        timed = df["timed_out"].sum()
        print(f"  Completed: {completed}, Timed out: {timed}")

        draw_opt_vs_exec_figure(df, display_name, FIGURES_DIR / f"{dataset_key}_dblog_opt_vs_exec.png")
        draw_phase_figure(df, display_name, FIGURES_DIR / f"{dataset_key}_dblog_phases.png")
        # Overwrite legacy per-dataset figure naming with db.log-based runtime plots.
        draw_runtime_naive_vs_optimized(df, display_name, FIGURES_DIR / f"{dataset_key}_naive_vs_optimized.png")

    # Cross-dataset timeout summary
    print("\nGenerating timeout summary figure...")
    draw_timeout_figure_all(all_data, FIGURES_DIR / "all_datasets_timeout_rate.png")
    print("Done.")


if __name__ == "__main__":
    main()
