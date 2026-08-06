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

For NRA/NIA, `--query-profile simple` keeps the original D7-D10 and D11/D13
register constraints without monotonic chains. The default
`--query-profile complex` adds monotonic chains while preserving the original
nonlinear constraints.
Simple-profile results use a `_simple` filename suffix.
Use `--query-profile both` to run and compare both profiles in one invocation;
NRA/NIA are executed twice, while LRA/LIA are executed once because their
queries are unchanged. Combined results use a `_both` filename suffix.

## Smoke Run

Example:

```bash
python3 integer-benchmark-d1d5-lia-lra/run_constraints_benchmark.py \
  --dataset ldbc01 \
  --sample-size 10 \
  --arith both \
  --timeout 10
```

To benchmark the simple NIA queries:

```bash
python3 integer-benchmark-d1d5-lia-lra/run_constraints_benchmark.py \
  --dataset pokec \
  --sample-size 10 \
  --arith nia \
  --query-profile simple \
  --timeout 10 \
  --no-rebuild
```


To run both NRA profiles together:

```bash
python3 integer-benchmark-d1d5-lia-lra/run_constraints_benchmark.py \
  --dataset pokec \
  --sample-size 10 \
  --arith nra \
  --query-profile both \
  --timeout 10 \
  --no-rebuild
```

Results are written under `integer-benchmark-d1d5-lia-lra/results/`.
