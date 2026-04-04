#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MDB_ROWS_CSV = ROOT / "figure" / "paper-reproduced-new-format" / "tables" / "execution_rows.csv"
OUT_DIR = ROOT / "figure" / "paper-reproduced-new-format" / "tables" / "neo4j_comparison"

NEO_RESULTS_ROOT = Path.home() / "research" / "neo4j-evaluation" / "results"

DATASET_CODE_TO_NEO = {
    "L1": "ldbc10",
    "L0": "ldbc01",
    "PO": "soc-pokec",
    "TE": "telecom",
    "IL": "icij-leak",
    "IP": "icij-paradise",
}
NEO_TO_DATASET_CODE = {v: k for k, v in DATASET_CODE_TO_NEO.items()}

REGULAR_LABEL_MAP = {
    "frequently_used": "Frequently-used",
    "occasionally_used": "Occasionally-used",
    "rarely_used": "Rarely-used",
}


def classify_neo_data_complexity(template: str) -> str | None:
    m = re.fullmatch(r"regular(\d+)", str(template).strip())
    if not m:
        return None
    rid = int(m.group(1))
    if rid in {1, 2}:
        return "Simple Data"
    if rid in {3, 4, 5}:
        return "Complex Data"
    return None


def classify_neo_regular_template(pattern: str) -> str | None:
    m = re.fullmatch(r"pattern(\d+)", str(pattern).strip())
    if not m:
        return None
    pid = int(m.group(1))
    if 1 <= pid <= 4:
        return "Frequently-used"
    if 5 <= pid <= 7:
        return "Occasionally-used"
    if 8 <= pid <= 12:
        return "Rarely-used"
    return None


def aggregate_stats(
    df: pd.DataFrame,
    timeout_col: str,
    duration_col: str,
    group_cols: list[str],
) -> pd.DataFrame:
    grouped_rows: list[dict] = []
    for key, g in df.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        item = {c: v for c, v in zip(group_cols, key)}

        timeout_series = g[timeout_col].astype(bool)
        durations = pd.to_numeric(g[duration_col], errors="coerce").dropna().astype(float)

        item["total_runs"] = int(len(g))
        item["timeout_runs"] = int(timeout_series.sum())
        item["timeout_ratio"] = float(timeout_series.mean()) if len(g) else np.nan

        if len(durations):
            # timeout-aware: include timeout runs in distributional statistics.
            item["top75_ms"] = float(np.nanpercentile(durations, 75))

            # Median of the slowest top 50% runs.
            threshold50 = float(np.nanpercentile(durations, 50))
            top_half = durations[durations >= threshold50]
            item["top50_median_ms"] = float(np.nanmedian(top_half)) if len(top_half) else np.nan

            # Median of the slowest top 25% runs.
            threshold = float(np.nanpercentile(durations, 75))
            top_quarter = durations[durations >= threshold]
            item["top25_median_ms"] = float(np.nanmedian(top_quarter)) if len(top_quarter) else np.nan
        else:
            item["top75_ms"] = np.nan
            item["top50_median_ms"] = np.nan
            item["top25_median_ms"] = np.nan

        grouped_rows.append(item)

    return pd.DataFrame(grouped_rows)


def load_mdb_stats() -> pd.DataFrame:
    if not MDB_ROWS_CSV.exists():
        raise FileNotFoundError(f"Missing MillenniumDB rows file: {MDB_ROWS_CSV}")

    df = pd.read_csv(MDB_ROWS_CSV)

    # Ensure booleans are interpreted correctly even if saved as strings.
    if df["timed_out"].dtype == object:
        df["timed_out"] = df["timed_out"].astype(str).str.strip().str.lower().isin(["1", "true", "t", "yes"])

    out_frames: list[pd.DataFrame] = []

    # Class 1: data complexity (Simple/Complex)
    dc = df[df["data_complexity"].notna()].copy()
    dc["class_type"] = "data_complexity"
    dc["class_label"] = dc["data_complexity"]
    dc["engine"] = "MillenniumDB"
    out_frames.append(
        aggregate_stats(
            dc,
            timeout_col="timed_out",
            duration_col="total_ms",
            group_cols=["dataset", "engine", "algorithm", "class_type", "class_label"],
        )
    )

    # Class 2: regular template class (Frequently/Occasionally/Rarely)
    rt = df[df["data_complexity"].notna()].copy()
    rt["class_type"] = "regular_template"
    rt["class_label"] = rt["regular_category"].map(REGULAR_LABEL_MAP)
    rt = rt[rt["class_label"].notna()].copy()
    rt["engine"] = "MillenniumDB"
    out_frames.append(
        aggregate_stats(
            rt,
            timeout_col="timed_out",
            duration_col="total_ms",
            group_cols=["dataset", "engine", "algorithm", "class_type", "class_label"],
        )
    )

    merged = pd.concat(out_frames, ignore_index=True)
    merged.rename(columns={"dataset": "dataset_code"}, inplace=True)
    merged["dataset_name"] = merged["dataset_code"].map(DATASET_CODE_TO_NEO)
    return merged


def collect_latest_neo_rows() -> pd.DataFrame:
    run_dirs = sorted(NEO_RESULTS_ROOT.glob("template_benchmark_*"))
    if not run_dirs:
        raise FileNotFoundError(f"No Neo4j benchmark run directories found under: {NEO_RESULTS_ROOT}")

    all_rows: list[pd.DataFrame] = []
    for run_dir in run_dirs:
        run_id = run_dir.name.replace("template_benchmark_", "")

        # Include both root-level aggregate csv and dataset-subdir csv files.
        for csv_path in run_dir.rglob("benchmark_results.csv"):
            try:
                temp = pd.read_csv(csv_path)
            except Exception:
                continue
            if temp.empty:
                continue
            temp["run_id"] = run_id
            temp["source_csv"] = str(csv_path)
            all_rows.append(temp)

    if not all_rows:
        raise RuntimeError("Found Neo4j run directories but no readable benchmark_results.csv files.")

    df = pd.concat(all_rows, ignore_index=True)

    # Normalize and drop exact duplicates introduced by root-level + per-dataset exports.
    dedupe_cols = [
        "run_id",
        "dataset",
        "start_id",
        "template",
        "pattern",
        "query_name",
        "duration_ms",
        "status",
    ]
    present = [c for c in dedupe_cols if c in df.columns]
    if present:
        df = df.drop_duplicates(subset=present)

    # Keep only latest run per dataset.
    df = df.sort_values("run_id")
    latest_run_per_dataset = df.groupby("dataset", as_index=False)["run_id"].max()
    df = df.merge(latest_run_per_dataset, on=["dataset", "run_id"], how="inner")

    return df


def load_neo_stats() -> pd.DataFrame:
    df = collect_latest_neo_rows()

    # Timeout semantics in Neo4j benchmark: status == 'timeout'.
    df["timed_out"] = df["status"].astype(str).str.lower().eq("timeout")

    df["dataset_code"] = df["dataset"].map(NEO_TO_DATASET_CODE)
    df = df[df["dataset_code"].notna()].copy()

    df["data_complexity"] = df["template"].map(classify_neo_data_complexity)
    df["regular_label"] = df["pattern"].map(classify_neo_regular_template)

    out_frames: list[pd.DataFrame] = []

    dc = df[df["data_complexity"].notna()].copy()
    dc["class_type"] = "data_complexity"
    dc["class_label"] = dc["data_complexity"]
    dc["engine"] = "Neo4j"
    dc["algorithm"] = "neo4j"
    out_frames.append(
        aggregate_stats(
            dc,
            timeout_col="timed_out",
            duration_col="duration_ms",
            group_cols=["dataset_code", "engine", "algorithm", "class_type", "class_label"],
        )
    )

    rt = df[df["regular_label"].notna()].copy()
    rt["class_type"] = "regular_template"
    rt["class_label"] = rt["regular_label"]
    rt["engine"] = "Neo4j"
    rt["algorithm"] = "neo4j"
    out_frames.append(
        aggregate_stats(
            rt,
            timeout_col="timed_out",
            duration_col="duration_ms",
            group_cols=["dataset_code", "engine", "algorithm", "class_type", "class_label"],
        )
    )

    merged = pd.concat(out_frames, ignore_index=True)
    merged["dataset_name"] = merged["dataset_code"].map(DATASET_CODE_TO_NEO)
    return merged


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mdb_stats = load_mdb_stats()
    neo_stats = load_neo_stats()

    all_stats = pd.concat([mdb_stats, neo_stats], ignore_index=True)
    all_stats = all_stats[
        [
            "dataset_code",
            "dataset_name",
            "engine",
            "algorithm",
            "class_type",
            "class_label",
            "total_runs",
            "timeout_runs",
            "timeout_ratio",
            "top50_median_ms",
            "top25_median_ms",
            "top75_ms",
        ]
    ].sort_values(["dataset_code", "class_type", "class_label", "engine", "algorithm"])

    all_stats.to_csv(OUT_DIR / "comparison_all_datasets.csv", index=False)

    # One table per dataset, as requested.
    for ds in sorted(all_stats["dataset_code"].dropna().unique()):
        ds_df = all_stats[all_stats["dataset_code"] == ds].copy()
        ds_df.to_csv(OUT_DIR / f"comparison_{ds}.csv", index=False)

    # Split tables for easier consumption.
    all_stats[all_stats["class_type"] == "data_complexity"].to_csv(
        OUT_DIR / "comparison_by_data_complexity.csv", index=False
    )
    all_stats[all_stats["class_type"] == "regular_template"].to_csv(
        OUT_DIR / "comparison_by_regular_template.csv", index=False
    )

    # Console summary.
    print("Neo4j + MillenniumDB comparison tables written to:", OUT_DIR)
    print("Datasets included:", ", ".join(sorted(all_stats["dataset_code"].dropna().unique())))
    print()
    print("=== Timeout Ratio / Top50% Median / Top25% Median / Top75 Runtime by data complexity ===")
    print(all_stats[all_stats["class_type"] == "data_complexity"].to_string(index=False))


if __name__ == "__main__":
    main()
