# Benchmark Summary From `db.log`

Date: Friday, July 31, 2026

This report summarizes the current benchmark results from the mode-specific `db.log` files under `integer-benchmark-d1d5-lia-lra/logs`.

Metrics:

- `timeout rate = timeout_count / (execution_count + timeout_count)`
- `average running time = mean of all "Execution : ... ms" entries`
- `median running time = median of all "Execution : ... ms" entries`

Caveat:

- The clean rerun started on Thursday, July 30, 2026 in `run_all_modes_lra_lia_20260730_clean.log`, but it stopped early.
- This summary therefore uses the completed per-mode `db.log` files currently on disk.
- Some `db.log` files also contain `Parsing Exception` lines; those counts are included for visibility, but the timeout-rate calculations below only use completed executions and explicit timeout events.

## Overall By Mode

| Mode | Executions | Timeouts | Parse Errors | Timeout Rate | Avg Exec Time (ms) | Median Exec Time (ms) |
|---|---:|---:|---:|---:|---:|---:|
| `subset` | 26,007 | 1,111 | 14,400 | 4.10% | 131.023 | 1.453 |
| `quantifier elimination` | 25,724 | 202 | 14,400 | 0.78% | 130.934 | 2.208 |
| `entailment with optimization` | 25,706 | 208 | 14,400 | 0.80% | 140.207 | 2.426 |

Takeaways:

- `quantifier elimination` has the lowest timeout rate.
- `entailment with optimization` is very close to `quantifier elimination` on timeout rate, but has the highest average execution time.
- `subset` has a much higher timeout rate than the other two modes.

## By Dataset And Mode

| Dataset | Mode | Executions | Timeouts | Parse Errors | Timeout Rate | Avg Exec Time (ms) | Median Exec Time (ms) |
|---|---|---:|---:|---:|---:|---:|---:|
| `icij-leak` | `subset` | 4,798 | 0 | 2,400 | 0.00% | 17.033 | 11.688 |
| `icij-leak` | `quantifier elimination` | 4,799 | 0 | 2,400 | 0.00% | 13.273 | 9.659 |
| `icij-leak` | `entailment with optimization` | 4,798 | 0 | 2,400 | 0.00% | 11.596 | 8.493 |
| `ldbc01` | `subset` | 4,800 | 0 | 2,400 | 0.00% | 1.906 | 0.020 |
| `ldbc01` | `quantifier elimination` | 4,799 | 0 | 2,400 | 0.00% | 0.215 | 0.019 |
| `ldbc01` | `entailment with optimization` | 4,799 | 1 | 2,400 | 0.02% | 0.283 | 0.020 |
| `ldbc10` | `subset` | 3,943 | 629 | 2,400 | 13.76% | 333.734 | 34.412 |
| `ldbc10` | `quantifier elimination` | 4,572 | 0 | 2,400 | 0.00% | 47.142 | 9.243 |
| `ldbc10` | `entailment with optimization` | 4,571 | 1 | 2,400 | 0.02% | 83.902 | 11.900 |
| `paradise` | `subset` | 3,600 | 0 | 2,400 | 0.00% | 2.698 | 0.681 |
| `paradise` | `quantifier elimination` | 2,400 | 0 | 2,400 | 0.00% | 3.285 | 0.029 |
| `paradise` | `entailment with optimization` | 2,400 | 0 | 2,400 | 0.00% | 2.105 | 0.029 |
| `pokec` | `subset` | 4,479 | 69 | 2,400 | 1.52% | 53.037 | 1.725 |
| `pokec` | `quantifier elimination` | 4,549 | 7 | 2,400 | 0.15% | 60.026 | 2.433 |
| `pokec` | `entailment with optimization` | 4,521 | 23 | 2,400 | 0.51% | 69.179 | 2.838 |
| `telecom` | `subset` | 4,387 | 413 | 2,400 | 8.60% | 399.697 | 8.124 |
| `telecom` | `quantifier elimination` | 4,605 | 195 | 2,400 | 4.06% | 609.545 | 0.028 |
| `telecom` | `entailment with optimization` | 4,617 | 183 | 2,400 | 3.81% | 616.381 | 0.030 |

## Short Interpretation

- `icij-leak`: `entailment with optimization` is best on both average running time and median running time, with no timeouts.
- `ldbc01`: `quantifier elimination` is clearly best, with essentially no timeouts.
- `ldbc10`: `quantifier elimination` is the best mode overall. `subset` is much worse and has a high timeout rate.
- `paradise`: `entailment with optimization` has the best average running time. No timeouts were observed.
- `pokec`: `subset` has the lowest average running time among successful runs, but `quantifier elimination` is much more stable on timeout rate.
- `telecom`: `subset` has lower average execution time on successful runs, but it times out much more often than `quantifier elimination` or `entailment with optimization`.

## Practical Summary

- If stability matters most, `quantifier elimination` is the best default mode from the current logs.
- If minimizing timeout rate is the priority, avoid `subset` on `ldbc10` and `telecom`.
- If minimizing average execution time on successful runs is the priority, the best mode depends heavily on the dataset.
