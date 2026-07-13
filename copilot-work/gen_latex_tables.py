import collections
import glob
import json
import math
import re

datasets = ["pokec", "ldbc01", "ldbc10", "paradise", "icij-leak", "telecom"]
ds_labels = {
    "pokec": "Pokec",
    "ldbc01": "LDBC-SF1",
    "ldbc10": "LDBC-SF10",
    "paradise": "Paradise",
    "icij-leak": "ICIJ",
    "telecom": "Telecom",
}

# --- Timeout rates from logs ---
base = "integer-benchmark-d1d5-lia-lra/logs"
timeout_counts = collections.defaultdict(lambda: collections.defaultdict(int))
total_counts = collections.defaultdict(lambda: collections.defaultdict(int))

for log_path in sorted(glob.glob(f"{base}/**/db.log", recursive=True)):
    parts = log_path.split("/")
    ds = parts[2]
    arith = parts[3].upper()
    var = parts[4]
    with open(log_path) as f:
        content = f.read()
    for blk in content.split("Query(")[1:]:
        m_timed = re.search(r"timed out after ([\d.]+) ms", blk)
        total_counts[ds][(arith, var)] += 1
        if m_timed:
            timeout_counts[ds][(arith, var)] += 1

# --- Alpha from comparison JSON ---
alpha_data = {}
alpha_overall = {}

for ds in datasets:
    with open(f"integer-benchmark-d1d5-lia-lra/results/{ds}_lra_lia_comparison.json") as f:
        data = json.load(f)
    comps = data["comparisons"]

    groups = collections.defaultdict(list)
    for c in comps:
        key = (c["arithmetic"], c["constraint_name"])
        # Cap at 10000ms (timeout threshold) instead of excluding
        opt_val = min(c.get("optimized_median_ms", 0), 10000)
        naive_val = min(c.get("naive_median_ms", 0), 10000)
        groups[key].append((opt_val, naive_val))

    for (arith, cstr), vals in groups.items():
        vals_opt = [v[0] for v in vals if v[0] > 0]
        vals_naive = [v[1] for v in vals if v[1] > 0]
        if vals_opt and vals_naive:
            geo_opt = math.exp(sum(math.log(v) for v in vals_opt) / len(vals_opt))
            geo_naive = math.exp(sum(math.log(v) for v in vals_naive) / len(vals_naive))
            alpha_data[(ds, arith, cstr)] = geo_naive / geo_opt

    for arith in ["LRA", "LIA"]:
        vals = []
        for c in comps:
            if c["arithmetic"] == arith:
                opt_val = min(c.get("optimized_median_ms", 0), 10000)
                naive_val = min(c.get("naive_median_ms", 0), 10000)
                vals.append((opt_val, naive_val))
        if vals:
            vals_opt = [v[0] for v in vals if v[0] > 0]
            vals_naive = [v[1] for v in vals if v[1] > 0]
            geo_opt = math.exp(sum(math.log(v) for v in vals_opt) / len(vals_opt))
            geo_naive = math.exp(sum(math.log(v) for v in vals_naive) / len(vals_naive))
            alpha_overall[(ds, arith)] = geo_naive / geo_opt


def bold_if(a):
    if a is not None and a > 1.0:
        return f"\\mathbf{{{a:.2f}}}"
    elif a is not None:
        return f"{a:.2f}"
    else:
        return "---"


lines = []

# ===== TABLE 1: Timeout Rates (datasets=rows, LRA/LIA=columns) =====
lines.append(r"\begin{table}[t]")
lines.append(r"\centering")
lines.append(r"\caption{Time-out rates (\%) of the naive and optimized algorithms.}")
lines.append(r"\label{tab:timeout-rates}")
lines.append(r"\small")
lines.append(r"\begin{tabular}{lrrrr}")
lines.append(r"\toprule")
lines.append(r"& \multicolumn{2}{c}{\textsc{LRA}} & \multicolumn{2}{c}{\textsc{LIA}} \\")
lines.append(r"\cmidrule(lr){2-3} \cmidrule(lr){4-5}")
lines.append(r"Dataset & Naive & Opt. & Naive & Opt. \\")
lines.append(r"\midrule")
for ds in datasets:
    row = ds_labels[ds]
    for arith in ["LRA", "LIA"]:
        for var in ["naive", "optimized"]:
            total = total_counts[ds].get((arith, var), 1)
            to = timeout_counts[ds].get((arith, var), 0)
            rate = 100 * to / total if total > 0 else 0
            row += f" & {rate:.1f}\\%"
    lines.append(row + r" \\")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table}")
lines.append("")

# ===== TABLE 2: Alpha (datasets=rows, LRA(D1,D2,D3,Overall)/LIA(D4,D5,D6,Overall)=columns) =====
lines.append(r"\begin{table}[t]")
lines.append(r"\centering")
lines.append(
    r"\caption{Proportional improvement $\alpha = \mathrm{GeoMean}(T_{\mathrm{naive}}) \,/\, \mathrm{GeoMean}(T_{\mathrm{optimized}})$.}"
)
lines.append(r"$\alpha > 1$ (bold) indicates the optimized algorithm is faster.")
lines.append(r"\label{tab:alpha}")
lines.append(r"\small")
lines.append(r"\begin{tabular}{lrrrrrrrr}")
lines.append(r"\toprule")
lines.append(r"& \multicolumn{4}{c}{\textsc{LRA}} & \multicolumn{4}{c}{\textsc{LIA}} \\")
lines.append(r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}")
lines.append(r"Dataset & D1 & D2 & D3 & Overall & D4 & D5 & D6 & Overall \\")
lines.append(r"\midrule")
for ds in datasets:
    row = ds_labels[ds]
    for arith, cstrs in [("LRA", ["D1", "D2", "D3"]), ("LIA", ["D4", "D5", "D6"])]:
        for cstr in cstrs:
            a = alpha_data.get((ds, arith, cstr))
            row += f" & {bold_if(a)}"
        a = alpha_overall.get((ds, arith))
        row += f" & {bold_if(a)}"
    lines.append(row + r" \\")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table}")

for line in lines:
    print(line)
