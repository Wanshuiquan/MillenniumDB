# Mean Running Time by Implementation Order

All times are arithmetic means in milliseconds. Each value is the mean of the
`mean_ms` rows for the corresponding dataset, arithmetic, and parser dispatch in
the latest `integer-benchmark-d1d5-lia-lra/results/*_all_both_trial.csv` files.
Every CSV row contains 100 runs. The lowest mean in each arithmetic row is
shown in **bold**.

## Linear arithmetic implementation mapping

The benchmark's three input variants are reported below by their actual
implementation dispatch rather than by the input labels `LIGHT`, `MID`, and
`HEAVY`.

| Arithmetic | `SUB` order | `QE` order | `MODEL` order |
|---|---|---|---|
| LRA | `LRA_SUB` / `NRA_SubsetOrder` | `LRA_QE` / `LRA` | `LRA_MODEL` / `RealModel` |
| LIA | `LIA_SUB` / `NIA_SubsetOrder` | `LIA_QE` / `LIA` | `LIA_MODEL` / `IntegerModel` |

This is the current routing. The existing CSV files predate the QE routing fix,
so their linear second and third variants both used model order. The linear
tables below retain those historical labels; a rerun is required to obtain QE
measurements.

## Non-linear arithmetic implementation mapping

| Arithmetic | `SUB` order | `MODEL` order | `MODEL_WITH_AI` order |
|---|---|---|---|
| NRA | `NRA_SUB` / `NRA_SubsetOrder` | `NRA_MODEL` / `RealModel` | `NRA_MODEL_WITH_AI` / `Real` |
| NIA | `NIA_SUB` / `NIA_SubsetOrder` | `NIA_MODEL` / `IntegerModel` | `NIA_MODEL_WITH_AI` / `Integer` |

For NRA and NIA, the third dispatch uses the distinct model-with-AI
implementation.

## icij-leak

### Linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order run 1 mean (ms) | `MODEL` order run 2 mean (ms) |
|---|---:|---:|---:|
| LRA | 19.537 | 15.628 | **14.841** |
| LIA | 30.664 | 32.095 | **24.506** |

### Non-linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order mean (ms) | `MODEL_WITH_AI` order mean (ms) |
|---|---:|---:|---:|
| NRA | 10.536 | 9.137 | **7.662** |
| NIA | 16.169 | 15.714 | **14.556** |

## paradise

### Linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order run 1 mean (ms) | `MODEL` order run 2 mean (ms) |
|---|---:|---:|---:|
| LRA | 13.113 | 5.309 | **5.034** |
| LIA | 6.133 | 5.164 | **5.111** |

### Non-linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order mean (ms) | `MODEL_WITH_AI` order mean (ms) |
|---|---:|---:|---:|
| NRA | 6.041 | **4.988** | 5.381 |
| NIA | **4.934** | 27.378 | 26.240 |

## ldbc01

### Linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order run 1 mean (ms) | `MODEL` order run 2 mean (ms) |
|---|---:|---:|---:|
| LRA | 16.967 | **3.267** | 3.319 |
| LIA | 9.788 | 8.335 | **4.601** |

### Non-linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order mean (ms) | `MODEL_WITH_AI` order mean (ms) |
|---|---:|---:|---:|
| NRA | 13.612 | **3.232** | 3.243 |
| NIA | 8.968 | **5.138** | 5.147 |

## ldbc10

### Linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order run 1 mean (ms) | `MODEL` order run 2 mean (ms) |
|---|---:|---:|---:|
| LRA | 4642.818 | 45.884 | **45.016** |
| LIA | 1788.767 | 56.658 | **45.409** |

### Non-linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order mean (ms) | `MODEL_WITH_AI` order mean (ms) |
|---|---:|---:|---:|
| NRA | 2100.307 | **30.319** | 33.348 |
| NIA | 1322.541 | **116.717** | 120.004 |

## pokec

### Linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order run 1 mean (ms) | `MODEL` order run 2 mean (ms) |
|---|---:|---:|---:|
| LRA | 205.408 | 88.989 | **59.711** |
| LIA | 645.445 | 55.805 | **41.340** |

### Non-linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order mean (ms) | `MODEL_WITH_AI` order mean (ms) |
|---|---:|---:|---:|
| NRA | 864.056 | **11.918** | 13.656 |
| NIA | 485.936 | **48.672** | 50.265 |

## telecom

### Linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order run 1 mean (ms) | `MODEL` order run 2 mean (ms) |
|---|---:|---:|---:|
| LRA | 1934.436 | 941.498 | **786.949** |
| LIA | 1151.602 | 728.997 | **682.787** |

### Non-linear arithmetic

| Arithmetic | `SUB` order mean (ms) | `MODEL` order mean (ms) | `MODEL_WITH_AI` order mean (ms) |
|---|---:|---:|---:|
| NRA | 2045.654 | 418.078 | **248.760** |
| NIA | 1201.565 | 623.516 | **532.620** |

## Source locations

- Parser-to-semantic mapping: `src/query/parser/grammar/mql/query_visitor.cc`
- Semantic-to-executor mapping: `src/query/optimizer/quad_model/plan/constraint_path_plan.cc`
- Benchmark results: `integer-benchmark-d1d5-lia-lra/results/`
