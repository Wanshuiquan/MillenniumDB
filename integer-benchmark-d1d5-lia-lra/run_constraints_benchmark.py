#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_SCRIPT_DIR = ROOT / "evaluation" / "script"
if str(EVAL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_SCRIPT_DIR))

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from evaluating.query import create_query_command  # type: ignore
from evaluating.util import (  # type: ignore
    get_mdb_server_memory,
    kill_server,
    sample,
    send_query,
    start_server,
)
from query_suite import CONSTRAINT_NAMES, LIA_CONSTRAINTS, LRA_CONSTRAINTS, QUERY_SPECS, TemplateQuery, build_constraint_queries


@dataclass
class QueryStat:
    dataset: str
    arithmetic: str
    variant: str
    template_id: int
    template_name: str
    constraint_name: str
    runs: int
    median_ms: float
    mean_ms: float
    max_memory_mb: float


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    source_qm: Path
    sample_bound: int
    candidate_query: str | None
    convert_numeric_attrs: bool
    scale: int = 1


def convert_qm_numeric_attrs(src: Path, dst: Path, scale: int = 1) -> dict:
    number_pattern = re.compile(r"(?<=:)\-?\d+\.\d+(?=(?:\s|$))")

    converted_values = 0
    total_lines = 0

    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("r", encoding="utf-8", errors="ignore") as fin, dst.open("w", encoding="utf-8") as fout:
        for line in fin:
            total_lines += 1

            def repl(match: re.Match[str]) -> str:
                nonlocal converted_values
                converted_values += 1
                value = float(match.group(0))
                return str(int(round(value * scale)))

            fout.write(number_pattern.sub(repl, line))

    return {
        "source": str(src),
        "output": str(dst),
        "total_lines": total_lines,
        "converted_numeric_values": converted_values,
    }


def build_db(qm_path: Path, db_dir: Path, skip_if_exists: bool = False) -> None:
    db_dir.parent.mkdir(parents=True, exist_ok=True)
    if db_dir.exists():
        if skip_if_exists:
            print(f"[build_db] Reusing existing DB: {db_dir}")
            return
        subprocess.run(["rm", "-rf", str(db_dir)], check=True)
    cmd = [str(ROOT / "build/Release/bin/mdb"), "import", str(qm_path), str(db_dir)]
    subprocess.run(cmd, check=True)


def get_dataset_config(dataset_name: str) -> DatasetConfig:
    if dataset_name == "pokec":
        return DatasetConfig(
            name="pokec",
            source_qm=ROOT / "evaluation" / "data" / "soc-pokec.qm",
            sample_bound=1_632_803,
            candidate_query=None,
            convert_numeric_attrs=True,
        )
    if dataset_name == "ldbc01":
        return DatasetConfig(
            name="ldbc01",
            source_qm=ROOT / "evaluation" / "data" / "ldbc01.qm",
            sample_bound=182_965,
            candidate_query=None,
            convert_numeric_attrs=False,
        )
    if dataset_name == "ldbc10":
        return DatasetConfig(
            name="ldbc10",
            source_qm=ROOT / "evaluation" / "data" / "ldbc10.qm",
            sample_bound=0,
            candidate_query=" Match (?s:Person) \n Return * \n",
            convert_numeric_attrs=False,
        )
    if dataset_name == "telecom":
        return DatasetConfig(
            name="telecom",
            source_qm=ROOT / "evaluation" / "data" / "telecom.qm",
            sample_bound=170_000,
            candidate_query=None,
            convert_numeric_attrs=True,
            scale=1000,
        )
    if dataset_name == "icij-leak":
        return DatasetConfig(
            name="icij-leak",
            source_qm=ROOT / "evaluation" / "data" / "icij-leak.qm",
            sample_bound=1_908_466,
            candidate_query=None,
            convert_numeric_attrs=False,
        )
    if dataset_name == "paradise":
        return DatasetConfig(
            name="paradise",
            source_qm=ROOT / "evaluation" / "data" / "icij-paradise.qm",
            sample_bound=163_414,
            candidate_query=None,
            convert_numeric_attrs=False,
        )
    raise ValueError(f"Unsupported dataset: {dataset_name}")


def prepare_lia_input(config: DatasetConfig, base_dir: Path) -> tuple[Path, dict]:
    if config.convert_numeric_attrs:
        converted_qm = base_dir / "data" / f"{config.name}.integer.qm"
        conversion_info = convert_qm_numeric_attrs(config.source_qm, converted_qm, scale=config.scale)
        return converted_qm, conversion_info
    return config.source_qm, {
        "source": str(config.source_qm),
        "output": str(config.source_qm),
        "total_lines": None,
        "converted_numeric_values": 0,
    }


def pick_candidates(
    sample_size: int, sample_bound: int, candidate_query: str | None, db_name: str, log_path: Path, timeout: int
) -> list[str]:
    if candidate_query is None:
        return [str(c) for c in sample(sample_size, sample_bound)]

    server = start_server(Path(db_name), timeout=timeout, log_path=log_path)
    try:
        response = send_query(candidate_query)
    finally:
        kill_server(server)

    if not isinstance(response, str):
        raise RuntimeError("Failed to retrieve candidate nodes for benchmark")

    rows = [line for line in response.splitlines() if line.strip()]
    if len(rows) <= 1:
        raise RuntimeError("Candidate query returned no rows")

    candidate_nodes = rows[1:]
    candidate_nodes = [c.lstrip("N") if c.startswith("N") else c for c in candidate_nodes]
    k = min(sample_size, len(candidate_nodes))
    return [str(c) for c in random.sample(candidate_nodes, k)]


def run_query_set(
    dataset: str,
    arithmetic: str,
    variant: str,
    db_name: str,
    queries: list[TemplateQuery],
    sample_size: int,
    sample_bound: int,
    candidate_query: str | None,
    log_path: Path,
    timeout: int,
) -> list[QueryStat]:
    stats: list[QueryStat] = []
    total_queries = len(queries)

    for query_idx, query_spec in enumerate(queries, start=1):
        print(
            f"[progress] {dataset} {arithmetic} {variant}: "
            f"query {query_idx}/{total_queries} "
            f"({query_spec.template_name} {query_spec.constraint_name})",
            flush=True,
        )
        candidates = pick_candidates(sample_size, sample_bound, candidate_query, db_name, log_path, timeout)
        runtimes: list[float] = []
        memories: list[float] = []
        server = start_server(Path(db_name), timeout=timeout, log_path=log_path)
        try:
            for sample_idx, idx in enumerate(candidates, start=1):
                if sample_idx == 1 or sample_idx == sample_size or sample_idx % 10 == 0:
                    print(
                        f"[progress] {dataset} {arithmetic} {variant}: "
                        f"{query_spec.template_name} {query_spec.constraint_name} "
                        f"sample {sample_idx}/{sample_size}",
                        flush=True,
                    )
                query = create_query_command(str(idx), query_spec.query)
                start_ns = time.time_ns()
                _ = send_query(query)
                end_ns = time.time_ns()
                runtimes.append((end_ns - start_ns) / 1_000_000)
                mem = get_mdb_server_memory()
                if mem is not None:
                    memories.append(mem)
        finally:
            kill_server(server)

        stats.append(
            QueryStat(
                dataset=dataset,
                arithmetic=arithmetic,
                variant=variant,
                template_id=query_spec.template_id,
                template_name=query_spec.template_name,
                constraint_name=query_spec.constraint_name,
                runs=len(runtimes),
                median_ms=statistics.median(runtimes),
                mean_ms=statistics.fmean(runtimes),
                max_memory_mb=max(memories) if memories else 0.0,
            )
        )

    return stats


def write_results(base_dir: Path, dataset: str, stats: list[QueryStat], meta: dict, suffix: str) -> None:
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / f"{dataset}_{suffix}_trial.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(
            [
                "dataset",
                "arithmetic",
                "variant",
                "template_id",
                "template_name",
                "constraint_name",
                "runs",
                "median_ms",
                "mean_ms",
                "max_memory_mb",
            ]
        )
        for row in stats:
            writer.writerow(
                [
                    row.dataset,
                    row.arithmetic,
                    row.variant,
                    row.template_id,
                    row.template_name,
                    row.constraint_name,
                    row.runs,
                    f"{row.median_ms:.6f}",
                    f"{row.mean_ms:.6f}",
                    f"{row.max_memory_mb:.6f}",
                ]
            )

    by_key: dict[tuple[str, str, int, str], QueryStat] = {}
    for row in stats:
        by_key[(row.arithmetic, row.variant, row.template_id, row.constraint_name)] = row

    comparisons = []
    constraints_by_arithmetic = {"LRA": LRA_CONSTRAINTS, "LIA": LIA_CONSTRAINTS}
    for arithmetic in {"LRA", "LIA"}:
        for template_id in range(1, 13):
            for constraint_name in constraints_by_arithmetic[arithmetic]:
                opt = by_key.get((arithmetic, "optimized", template_id, constraint_name))
                nai = by_key.get((arithmetic, "naive", template_id, constraint_name))
                if opt is None or nai is None or opt.median_ms == 0:
                    continue
                comparisons.append(
                    {
                        "arithmetic": arithmetic,
                        "template_id": template_id,
                        "template_name": opt.template_name,
                        "constraint_name": constraint_name,
                        "optimized_median_ms": opt.median_ms,
                        "naive_median_ms": nai.median_ms,
                        "speedup_naive_over_optimized": nai.median_ms / opt.median_ms,
                        "optimized_better": nai.median_ms / opt.median_ms > 1.0,
                    }
                )

    with (results_dir / f"{dataset}_{suffix}_comparison.json").open("w", encoding="utf-8") as fout:
        json.dump(
            {
                "dataset": dataset,
                "meta": meta,
                "global_max_memory_mb": max((s.max_memory_mb for s in stats), default=0.0),
                "comparisons": comparisons,
            },
            fout,
            indent=2,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark 12 regular templates x 6 data constraints for LRA and LIA."
    )
    parser.add_argument(
        "--dataset",
        choices=["pokec", "ldbc01", "ldbc10", "telecom", "icij-leak", "paradise", "both", "all", "extra4"],
        default="both",
    )
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--arith", choices=["lra", "lia", "both"], default="both")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help="Skip rebuilding databases that already exist on disk.",
    )
    args = parser.parse_args()

    base_dir = ROOT / "integer-benchmark-d1d5-lia-lra"

    if args.dataset == "both":
        datasets = ["pokec", "ldbc01"]
    elif args.dataset == "all":
        datasets = ["pokec", "ldbc01", "ldbc10", "telecom", "icij-leak", "paradise"]
    elif args.dataset == "extra4":
        datasets = ["ldbc10", "telecom", "icij-leak", "paradise"]
    else:
        datasets = [args.dataset]

    run_lra = args.arith in {"lra", "both"}
    run_lia = args.arith in {"lia", "both"}

    suffix = "lra_lia"
    if args.arith == "lra":
        suffix = "lra"
    elif args.arith == "lia":
        suffix = "lia"

    for dataset_name in datasets:
        print(f"[progress] starting dataset {dataset_name}", flush=True)
        config = get_dataset_config(dataset_name)
        spec = QUERY_SPECS[dataset_name]

        lia_input, conversion_info = prepare_lia_input(config, base_dir)
        lra_input = config.source_qm

        db_lra = base_dir / "database" / f"{dataset_name}_lra"
        db_lia = base_dir / "database" / f"{dataset_name}_lia"

        if run_lra:
            print(f"[progress] {dataset_name}: preparing LRA database", flush=True)
            build_db(lra_input, db_lra, skip_if_exists=args.no_rebuild)
        if run_lia:
            print(f"[progress] {dataset_name}: preparing LIA database", flush=True)
            build_db(lia_input, db_lia, skip_if_exists=args.no_rebuild)

        stats: list[QueryStat] = []

        if run_lra:
            print(f"[progress] {dataset_name}: starting LRA optimized", flush=True)
            opt_lra = build_constraint_queries(spec, optimized=True, integer_mode=False, scale=1)
            nai_lra = build_constraint_queries(spec, optimized=False, integer_mode=False, scale=1)
            stats.extend(
                run_query_set(
                    dataset=dataset_name,
                    arithmetic="LRA",
                    variant="optimized",
                    db_name=str(db_lra),
                    queries=opt_lra,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "lra" / "optimized" / "db.log",
                    timeout=args.timeout,
                )
            )
            print(f"[progress] {dataset_name}: starting LRA naive", flush=True)
            stats.extend(
                run_query_set(
                    dataset=dataset_name,
                    arithmetic="LRA",
                    variant="naive",
                    db_name=str(db_lra),
                    queries=nai_lra,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "lra" / "naive" / "db.log",
                    timeout=args.timeout,
                )
            )

        if run_lia:
            print(f"[progress] {dataset_name}: starting LIA optimized", flush=True)
            opt_lia = build_constraint_queries(spec, optimized=True, integer_mode=True, scale=config.scale)
            nai_lia = build_constraint_queries(spec, optimized=False, integer_mode=True, scale=config.scale)
            stats.extend(
                run_query_set(
                    dataset=dataset_name,
                    arithmetic="LIA",
                    variant="optimized",
                    db_name=str(db_lia),
                    queries=opt_lia,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "lia" / "optimized" / "db.log",
                    timeout=args.timeout,
                )
            )
            print(f"[progress] {dataset_name}: starting LIA naive", flush=True)
            stats.extend(
                run_query_set(
                    dataset=dataset_name,
                    arithmetic="LIA",
                    variant="naive",
                    db_name=str(db_lia),
                    queries=nai_lia,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "lia" / "naive" / "db.log",
                    timeout=args.timeout,
                )
            )

        query_dump = {
            "lra": {query.query_key: query.query for query in opt_lra} if run_lra else {},
            "lia": {query.query_key: query.query for query in opt_lia} if run_lia else {},
        }
        meta = {
            "timeout_seconds": args.timeout,
            "sample_size": args.sample_size,
            "regular_template_count": 12,
            "constraint_count": len(CONSTRAINT_NAMES),
            "lra_constraint_count": len(LRA_CONSTRAINTS),
            "lia_constraint_count": len(LIA_CONSTRAINTS),
            "lra_constraints": list(LRA_CONSTRAINTS),
            "lia_constraints": list(LIA_CONSTRAINTS),
            "query_instances_per_constraint": 12 * args.sample_size,
            "lia_conversion": conversion_info,
            "queries": query_dump,
        }
        write_results(base_dir, dataset_name, stats, meta, suffix)
        print(f"[done] {dataset_name}: wrote {len(stats)} benchmark rows")


if __name__ == "__main__":
    main()
