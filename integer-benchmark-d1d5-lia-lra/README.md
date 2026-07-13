# D1/D5 Constraint Benchmark

This benchmark directory is a standalone variant of `integer-benchmark` for:

- `D1` from Table 4 in `evaluation/paper_draft/main.pdf`
- `D5` from Table 4 in `evaluation/paper_draft/main.pdf`
- `different_from_first`
- `increasing_by_1`
- `sum_below_threshold`
- `odd_even_repeat`

## Design

The new constraints are benchmarked on a fixed 3-edge / 4-node chain per dataset.
That choice keeps all six constraints expressible with the current `DATA_TEST`
syntax and the register feature (`??name`).

`D1` and `D5` are encoded directly from the paper-style definitions rather than
reusing the older benchmark formulas verbatim.

The benchmark runner supports:

- `LRA` via `DATA_TEST REAL`
- `LIA` via `DATA_TEST INT`
- naive execution via `DATA_TEST NAIVE`

## Smoke Run

Example:

```bash
python3 integer-benchmark-d1d5-lia-lra/run_constraints_benchmark.py \
  --dataset ldbc01 \
  --sample-size 10 \
  --arith both \
  --timeout 10
```

Results are written under `integer-benchmark-d1d5-lia-lra/results/`.
