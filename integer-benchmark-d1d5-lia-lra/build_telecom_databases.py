#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THIS_DIR = Path(__file__).resolve().parent

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from run_constraints_benchmark import build_db, get_dataset_config, prepare_lia_input


def main() -> None:
    base_dir = ROOT / "integer-benchmark-d1d5-lia-lra"
    config = get_dataset_config("telecom")

    lia_input, conversion_info = prepare_lia_input(config, base_dir)
    print(f"[telecom-build] conversion_info={conversion_info}", flush=True)

    build_db(config.source_qm, base_dir / "database" / "telecom_lra", skip_if_exists=False)
    build_db(lia_input, base_dir / "database" / "telecom_lia", skip_if_exists=False)

    print("[telecom-build] completed", flush=True)


if __name__ == "__main__":
    main()
