# Query And Result Structure

## Scope

This note documents the current structure of the benchmark queries and the output result files used by:

- `integer-benchmark-d1d5-lia-lra/query_suite.py`
- `integer-benchmark-d1d5-lia-lra/run_constraints_benchmark.py`

It reflects the current benchmark policy:

- `LRA` runs only `D1`, `D2`, `D3`
- `LIA` runs only `D4`, `D5`, `D6`
- each arithmetic mode uses `12` regular templates
- each regular template is instantiated with `sample-size` concrete start nodes

## Query Structure

### High-level composition

Each benchmark query is defined by:

1. a dataset-specific graph schema choice
2. one regular template from `regular01` to `regular12`
3. one data constraint
4. one arithmetic mode:
   - `DATA_TEST REAL ?e` for optimized `LRA`
   - `DATA_TEST INT ?e` for optimized `LIA`
   - `DATA_TEST NAIVE ?e` for naive execution
5. one concrete start node injected through:

```text
Match (N<start_id>) =[<query>] => (?to)
Return *
Limit 1
```

### Arithmetic split

#### LRA constraints

- `D1`: there exists a 2D point within Manhattan distance `d` from each node on the path
- `D2`: each 2D vector on the path is different from the start point but remains within distance `d` of the start point
- `D3`: there exists a scalar point `x` within distance `d` of each node, and `x` is smaller than the end-point value by `c`

#### LIA constraints

- `D4`: path values of property `p` are increasing and stay within range `c`
- `D5`: path values of property `p` are decreasing and the end-point `p` value is even
- `D6`: the end-point value `pe` is even and every node value is at most half of `pe`

### Regular templates

The benchmark uses `12` regular templates named:

- `regular01`
- `regular02`
- `regular03`
- `regular04`
- `regular05`
- `regular06`
- `regular07`
- `regular08`
- `regular09`
- `regular10`
- `regular11`
- `regular12`

These templates are dataset-agnostic skeletons built from the dataset's:

- `node_labels`
- `edge_labels`
- numeric attributes `attr1` and `attr2`

### Dataset-specific specification

Each dataset contributes:

- `node_labels`: a 4-node tuple used by the regular templates
- `edge_labels`: a 3-edge tuple used by the regular templates
- `attr1`, `attr2`: numeric properties used in data constraints
- thresholds:
  - `two_d_threshold`
  - `scalar_threshold`
  - `end_gap`
  - `range_threshold`

Examples:

- `ldbc01`
  - nodes: `person`, `person`, `tag`, `tagclass`
  - edges: `:knows`, `:hasInterest`, `:hasType`
  - attributes: `oid`, `iid`
- `paradise`
  - nodes: `Officer`, `Entity`, `Address`, `Intermediary`
  - edges: `:OFFICER_OF`, `:REGISTERED_ADDRESS`, `:INTERMEDIARY_OF`
  - attributes: `node_id`, `valid_until`

### Query counts

For a run with `--arith both`:

- `LRA`
  - `12 templates x 3 constraints = 36 query templates`
- `LIA`
  - `12 templates x 3 constraints = 36 query templates`
- total
  - `72 query templates`

For a run with sample size `N`:

- `LRA` executes `36 x N` concrete queries per variant
- `LIA` executes `36 x N` concrete queries per variant
- with both `optimized` and `naive`, total concrete executions are:
  - `72 x N x 2`

For `N = 100`:

- per arithmetic side and variant:
  - `3600` concrete executions
- total for `--arith both` and both variants:
  - `7200` concrete executions

## Result Structure

### Output directory

All benchmark result files are written under:

- `integer-benchmark-d1d5-lia-lra/results/`

### Trial CSV

Per dataset, the main raw summary file is:

- `<dataset>_lra_lia_trial.csv`

If only one arithmetic mode is requested:

- `<dataset>_lra_trial.csv`
- `<dataset>_lia_trial.csv`

#### CSV columns

The trial CSV contains:

- `dataset`
- `arithmetic`
- `variant`
- `template_id`
- `template_name`
- `constraint_name`
- `runs`
- `median_ms`
- `mean_ms`
- `max_memory_mb`

#### Meaning of one CSV row

One row corresponds to one:

- dataset
- arithmetic mode
- execution variant
- regular template
- data constraint

The `runs` column is the number of sampled start nodes used for that row.

With the current split mode and `--arith both`, each dataset should produce:

- `12 templates x 3 LRA constraints x 2 variants = 72 rows` for `LRA`
- `12 templates x 3 LIA constraints x 2 variants = 72 rows` for `LIA`
- total:
  - `144` rows

### Comparison JSON

Per dataset, the comparison file is:

- `<dataset>_lra_lia_comparison.json`

It contains:

- `dataset`
- `meta`
- `global_max_memory_mb`
- `comparisons`

#### Meta fields

Important metadata fields include:

- `timeout_seconds`
- `sample_size`
- `regular_template_count`
- `constraint_count`
- `lra_constraint_count`
- `lia_constraint_count`
- `lra_constraints`
- `lia_constraints`
- `query_instances_per_constraint`
- `lia_conversion`
- `queries`

#### queries object

The `queries` section stores the generated query templates by arithmetic side:

- `queries.lra`
- `queries.lia`

Each entry is keyed by:

```text
regularXX:DY
```

Example keys:

- `regular01:D1`
- `regular05:D3`
- `regular12:D6`

The value is the exact query string sent into the benchmark runner before start-node injection.

#### comparisons array

Each object in `comparisons` is a pairwise optimized-vs-naive comparison for one:

- arithmetic mode
- template
- data constraint

It includes:

- `arithmetic`
- `template_id`
- `template_name`
- `constraint_name`
- `optimized_median_ms`
- `naive_median_ms`
- `speedup_naive_over_optimized`
- `optimized_better`

With the current split mode and `--arith both`, each dataset should produce:

- `12 x 3 = 36` comparisons for `LRA`
- `12 x 3 = 36` comparisons for `LIA`
- total:
  - `72` comparison records

## Progress Output

The runner now prints progress messages for:

- dataset start
- database preparation
- arithmetic/variant phase start
- query-template progress
- sample progress inside each query-template batch

Typical output looks like:

```text
[progress] starting dataset ldbc01
[progress] ldbc01: preparing LRA database
[progress] ldbc01: starting LRA optimized
[progress] ldbc01 LRA optimized: query 7/36 (regular03 D1)
[progress] ldbc01 LRA optimized: regular03 D1 sample 10/100
```

## Related Files

- [query_suite.py](/home/heyang-li/research/MillenniumDB/integer-benchmark-d1d5-lia-lra/query_suite.py)
- [run_constraints_benchmark.py](/home/heyang-li/research/MillenniumDB/integer-benchmark-d1d5-lia-lra/run_constraints_benchmark.py)
- [ldbc01_lra_lia_trial.csv](/home/heyang-li/research/MillenniumDB/integer-benchmark-d1d5-lia-lra/results/ldbc01_lra_lia_trial.csv)
- [ldbc01_lra_lia_comparison.json](/home/heyang-li/research/MillenniumDB/integer-benchmark-d1d5-lia-lra/results/ldbc01_lra_lia_comparison.json)
