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

# Query templates live in integer-benchmark/queries/ (0.5 * replaced with 5 *)
_QUERIES_DIR = Path(__file__).resolve().parent
if str(_QUERIES_DIR) not in sys.path:
    sys.path.insert(0, str(_QUERIES_DIR))

from evaluating.query import create_query_command  # type: ignore
from evaluating.util import (  # type: ignore
    get_mdb_server_memory,
    kill_server,
    sample,
    send_query,
    start_server,
)
from queries import (  # noqa: E402
    icijleak,
    icijleak_naive,
    ldbc01,
    ldbc01_naive,
    ldbc10,
    ldbc10_naive,
    paradise,
    paradise_naive,
    pokec,
    pokec_naive,
    telecom,
    telecom_naive,
)


@dataclass
class QueryStat:
    dataset: str
    arithmetic: str
    variant: str
    query_kind: str
    template_index: int
    query_index: int
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
    regex_templates: list[str]
    optimized_rdpq_templates: list[list[str]]
    naive_rdpq_templates: list[list[str]]
    convert_numeric_attrs: bool
    scale: int = 1  # multiply attr values by this factor when converting (e.g. 1000 for [0,1] floats)


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


def lia_transform(query: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return str(int(round(float(match.group(0)))))

    return re.sub(r"(?<![\w.])\-?\d+\.\d+", repl, query)


def nia_transform(query: str) -> str:
    q = lia_transform(query)

    def transform_predicate(pred: str) -> str:
        if "*" in pred or "/" in pred:
            return pred.replace("+", "*")
        return pred.replace("+", "*").replace("-", "*")

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        return "{" + transform_predicate(inner) + "}"

    return re.sub(r"\{([^{}]*)\}", repl, q)


def build_db(qm_path: Path, db_dir: Path, skip_if_exists: bool = False) -> None:
    db_dir.parent.mkdir(parents=True, exist_ok=True)
    if db_dir.exists():
        if skip_if_exists:
            print(f"[build_db] Skipping rebuild of existing DB: {db_dir}")
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
            regex_templates=pokec.REGEX_TEMPLATE,
            optimized_rdpq_templates=pokec.RDPQ_TEMPLATE,
            naive_rdpq_templates=pokec_naive.RDPQ_TEMPLATE,
            convert_numeric_attrs=True,
        )
    if dataset_name == "ldbc01":
        return DatasetConfig(
            name="ldbc01",
            source_qm=ROOT / "evaluation" / "data" / "ldbc01.qm",
            sample_bound=182_965,
            candidate_query=None,
            regex_templates=ldbc01.REGEX_TEMPLATE,
            optimized_rdpq_templates=ldbc01.RDPQ_TEMPLATE,
            naive_rdpq_templates=ldbc01_naive.RDPQ_TEMPLATE,
            convert_numeric_attrs=False,
        )
    if dataset_name == "ldbc10":
        return DatasetConfig(
            name="ldbc10",
            source_qm=ROOT / "evaluation" / "data" / "ldbc10.qm",
            sample_bound=0,
            candidate_query=" Match (?s:Person) \n Return * \n",
            regex_templates=ldbc10.REGEX_TEMPLATE,
            optimized_rdpq_templates=ldbc10.RDPQ_TEMPLATE,
            naive_rdpq_templates=ldbc10_naive.RDPQ_TEMPLATE,
            convert_numeric_attrs=False,
        )
    if dataset_name == "telecom":
        return DatasetConfig(
            name="telecom",
            source_qm=ROOT / "evaluation" / "data" / "telecom.qm",
            sample_bound=170_000,
            candidate_query=None,
            regex_templates=telecom.REGEX_TEMPLATE,
            optimized_rdpq_templates=telecom.RDPQ_TEMPLATE,
            naive_rdpq_templates=telecom_naive.RDPQ_TEMPLATE,
            convert_numeric_attrs=True,
            scale=1000,
        )
    if dataset_name == "icij-leak":
        return DatasetConfig(
            name="icij-leak",
            source_qm=ROOT / "evaluation" / "data" / "icij-leak.qm",
            sample_bound=1_908_466,
            candidate_query=None,
            regex_templates=icijleak.REGEX_TEMPLATE,
            optimized_rdpq_templates=icijleak.RDPQ_TEMPLATE,
            naive_rdpq_templates=icijleak_naive.RDPQ_TEMPLATE,
            convert_numeric_attrs=False,
        )
    if dataset_name == "paradise":
        return DatasetConfig(
            name="paradise",
            source_qm=ROOT / "evaluation" / "data" / "icij-paradise.qm",
            sample_bound=163_414,
            candidate_query=None,
            regex_templates=paradise.REGEX_TEMPLATE,
            optimized_rdpq_templates=paradise.RDPQ_TEMPLATE,
            naive_rdpq_templates=paradise_naive.RDPQ_TEMPLATE,
            convert_numeric_attrs=False,
        )
    raise ValueError(f"Unsupported dataset: {dataset_name}")


def pick_candidates(
    sample_size: int, sample_bound: int, candidate_query: str | None, db_name: str, log_path: Path
) -> list[str]:
    if candidate_query is None:
        return [str(c) for c in sample(sample_size, sample_bound)]

    server = start_server(Path(db_name), log_path=log_path)
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
    if not candidate_nodes:
        raise RuntimeError("Candidate query returned no node identifiers")

    # Node IDs returned by queries have an "N" prefix (e.g. "N22497762"), but
    # create_query_command already prepends "N", so strip it to avoid "NN..." IDs.
    candidate_nodes = [c.lstrip("N") if c.startswith("N") else c for c in candidate_nodes]

    k = min(sample_size, len(candidate_nodes))
    return [str(c) for c in random.sample(candidate_nodes, k)]


def prepare_dataset_input(config: DatasetConfig, base_dir: Path) -> tuple[Path, dict]:
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


def run_single_query_set(
    dataset: str,
    arithmetic: str,
    variant: str,
    db_name: str,
    regex_templates: list[str],
    rdpq_templates: list[list[str]],
    template_count: int,
    sample_size: int,
    sample_bound: int,
    candidate_query: str | None,
    log_path: Path,
) -> list[QueryStat]:
    stats: list[QueryStat] = []
    candidates = pick_candidates(sample_size, sample_bound, candidate_query, db_name, log_path)

    for template_index in range(template_count):
        regex_template = regex_templates[template_index]

        regex_times: list[float] = []
        regex_mem: list[float] = []
        server = start_server(Path(db_name), log_path=log_path)
        for idx in candidates:
            query = create_query_command(str(idx), regex_template)
            start_ns = time.time_ns()
            _ = send_query(query)
            end_ns = time.time_ns()
            regex_times.append((end_ns - start_ns) / 1_000_000)
            mem = get_mdb_server_memory()
            if mem is not None:
                regex_mem.append(mem)
        kill_server(server)

        stats.append(
            QueryStat(
                dataset=dataset,
                arithmetic=arithmetic,
                variant=variant,
                query_kind="regex",
                template_index=template_index + 1,
                query_index=0,
                runs=len(regex_times),
                median_ms=statistics.median(regex_times),
                mean_ms=statistics.fmean(regex_times),
                max_memory_mb=max(regex_mem) if regex_mem else 0.0,
            )
        )

        for query_index, query_template in enumerate(rdpq_templates[template_index], start=1):
            rdpq_times: list[float] = []
            rdpq_mem: list[float] = []
            server = start_server(Path(db_name), log_path=log_path)
            for idx in candidates:
                query = create_query_command(str(idx), query_template)
                start_ns = time.time_ns()
                _ = send_query(query)
                end_ns = time.time_ns()
                rdpq_times.append((end_ns - start_ns) / 1_000_000)
                mem = get_mdb_server_memory()
                if mem is not None:
                    rdpq_mem.append(mem)
            kill_server(server)

            stats.append(
                QueryStat(
                    dataset=dataset,
                    arithmetic=arithmetic,
                    variant=variant,
                    query_kind="rdpq",
                    template_index=template_index + 1,
                    query_index=query_index,
                    runs=len(rdpq_times),
                    median_ms=statistics.median(rdpq_times),
                    mean_ms=statistics.fmean(rdpq_times),
                    max_memory_mb=max(rdpq_mem) if rdpq_mem else 0.0,
                )
            )

    return stats


def write_results(base_dir: Path, dataset: str, stats: list[QueryStat], conversion_info: dict, suffix: str) -> None:
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
                "query_kind",
                "template_index",
                "query_index",
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
                    row.query_kind,
                    row.template_index,
                    row.query_index,
                    row.runs,
                    f"{row.median_ms:.6f}",
                    f"{row.mean_ms:.6f}",
                    f"{row.max_memory_mb:.6f}",
                ]
            )

    optimized = {}
    naive = {}
    for row in stats:
        key = (row.arithmetic, row.query_kind, row.template_index, row.query_index)
        if row.variant == "optimized":
            optimized[key] = row
        else:
            naive[key] = row

    comparisons = []
    for key, opt in optimized.items():
        nai = naive.get(key)
        if nai is None or opt.median_ms == 0:
            continue
        speedup = nai.median_ms / opt.median_ms
        comparisons.append(
            {
                "arithmetic": key[0],
                "query_kind": key[1],
                "template_index": key[2],
                "query_index": key[3],
                "optimized_median_ms": opt.median_ms,
                "naive_median_ms": nai.median_ms,
                "speedup_naive_over_optimized": speedup,
                "optimized_better": speedup > 1.0,
            }
        )

    with (results_dir / f"{dataset}_{suffix}_comparison.json").open("w", encoding="utf-8") as fout:
        json.dump(
            {
                "dataset": dataset,
                "conversion": conversion_info,
                "global_max_memory_mb": max((s.max_memory_mb for s in stats), default=0.0),
                "comparisons": comparisons,
            },
            fout,
            indent=2,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LIA/NIA benchmark trials with benchmark-local db logs.")
    parser.add_argument(
        "--dataset",
        choices=["pokec", "ldbc01", "ldbc10", "telecom", "icij-leak", "paradise", "both", "all", "extra4"],
        default="both",
    )
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--template-count", type=int, default=2)
    parser.add_argument("--arith", choices=["lra", "lia", "nia", "both"], default="both")
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help="Skip rebuilding databases that already exist on disk.",
    )
    args = parser.parse_args()

    if args.template_count < 1 or args.template_count > len(pokec.REGEX_TEMPLATE):
        raise ValueError("template-count must be in [1, 12]")

    base_dir = ROOT / "integer-benchmark"

    run_lia = args.arith in {"lia", "lra", "both"}
    run_nia = args.arith in {"nia", "both"}

    suffix = "lia_nia"
    if args.arith in {"lia", "lra"}:
        suffix = "lra"
    elif args.arith == "nia":
        suffix = "nia"

    if args.dataset == "both":
        datasets = ["pokec", "ldbc01"]
    elif args.dataset == "all":
        datasets = ["pokec", "ldbc01", "ldbc10", "telecom", "icij-leak", "paradise"]
    elif args.dataset == "extra4":
        datasets = ["ldbc10", "telecom", "icij-leak", "paradise"]
    else:
        datasets = [args.dataset]

    for dataset_name in datasets:
        config = get_dataset_config(dataset_name)
        qm_input, conversion_info = prepare_dataset_input(config, base_dir)

        db_lia = base_dir / "database" / f"{dataset_name}_lia"
        db_nia = base_dir / "database" / f"{dataset_name}_nia"

        if run_lia:
            build_db(qm_input, db_lia, skip_if_exists=args.no_rebuild)
        if run_nia:
            build_db(qm_input, db_nia, skip_if_exists=args.no_rebuild)

        regex_lia = [lia_transform(q) for q in config.regex_templates]
        regex_nia = [nia_transform(q) for q in config.regex_templates]

        rdpq_opt_lia = [[lia_transform(q) for q in group] for group in config.optimized_rdpq_templates]
        rdpq_opt_nia = [[nia_transform(q) for q in group] for group in config.optimized_rdpq_templates]

        rdpq_nai_lia = [[lia_transform(q) for q in group] for group in config.naive_rdpq_templates]
        rdpq_nai_nia = [[nia_transform(q) for q in group] for group in config.naive_rdpq_templates]

        stats: list[QueryStat] = []

        if run_lia:
            stats.extend(
                run_single_query_set(
                    dataset=dataset_name,
                    arithmetic="LIA",
                    variant="optimized",
                    db_name=str(db_lia),
                    regex_templates=regex_lia,
                    rdpq_templates=rdpq_opt_lia,
                    template_count=args.template_count,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "lia" / "optimized" / "db.log",
                )
            )
            stats.extend(
                run_single_query_set(
                    dataset=dataset_name,
                    arithmetic="LIA",
                    variant="naive",
                    db_name=str(db_lia),
                    regex_templates=regex_lia,
                    rdpq_templates=rdpq_nai_lia,
                    template_count=args.template_count,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "lia" / "naive" / "db.log",
                )
            )

        if run_nia:
            stats.extend(
                run_single_query_set(
                    dataset=dataset_name,
                    arithmetic="NIA",
                    variant="optimized",
                    db_name=str(db_nia),
                    regex_templates=regex_nia,
                    rdpq_templates=rdpq_opt_nia,
                    template_count=args.template_count,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "nia" / "optimized" / "db.log",
                )
            )
            stats.extend(
                run_single_query_set(
                    dataset=dataset_name,
                    arithmetic="NIA",
                    variant="naive",
                    db_name=str(db_nia),
                    regex_templates=regex_nia,
                    rdpq_templates=rdpq_nai_nia,
                    template_count=args.template_count,
                    sample_size=args.sample_size,
                    sample_bound=config.sample_bound,
                    candidate_query=config.candidate_query,
                    log_path=base_dir / "logs" / dataset_name / "nia" / "naive" / "db.log",
                )
            )

        write_results(base_dir, dataset_name, stats, conversion_info, suffix)


if __name__ == "__main__":
    main()
