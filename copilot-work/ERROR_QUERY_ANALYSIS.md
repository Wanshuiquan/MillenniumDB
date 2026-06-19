# Error Query Analysis Report

## Executive Summary
Reran all **68 error queries** from the data-4 Q4 variant. **All 68 queries STILL FAIL** with deterministic exceptions, confirming the errors are reproducible and not random.

## Key Findings

### 1. Error Queries are 100% Deterministic
- **Total error queries extracted**: 68 unique node IDs
- **Rerun success rate**: 0/68 (0%)
- **Rerun failure rate**: 68/68 (100%)
- **Conclusion**: The "expression is not a string literal" exception is consistently reproducible

### 2. Error Query Characteristics
All 68 queries use the **same query template**:
```
Match (N{node_id}) =[DATA_TEST ?e (cell {?p == attr1 and ?q == attr2})/ 
    (((:lived {true}) | (:used {true}) | (:bought {true}))/(user {?q - attr2 <= 0.1 and 
    attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p})))*] Return * Limit 1
```

**Formula Pattern**:
- Cell constraint: `?p == attr1 and ?q == attr2`
- User constraint: `?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p`
- Variables: `?p`, `?q` (query variables)
- Attributes: `attr1`, `attr2` (node properties)

### 3. Error Node IDs (68 total)
```
N100105    N103247    N103659    N104023    N107652    N108752    N111501
N111869    N112420    N115802    N115813    N119061    N119267    N123914
N124879    N126171    N12664     N13166     N133329    N133593    N135069
N136576    N136811    N136927    N137318    N140647    N143587    N144557
N144737    N146254    N147600    N148999    N149061    N150999    N154207
N154342    N157323    N158833    N158859    N160272    N161955    N162616
N168411    N24046     N25551     N29310     N34005     N3615      N38536
N38958     N41198     N50250     N50944     N53685     N55424     N5771
N62426     N63542     N65572     N67099     N76378     N86116     N87995
N92825     N94394     N96401     N98624     N9876
```

## Root Cause Analysis

### Problem Hierarchy
1. **Z3 Parsing Exception** (symptom)
   - Message: "expression is not a string literal"
   - Location: `src/query/executor/binding_iter/paths/data_test/lra/bfs_enum.cc:63`
   
2. **Formula Variable Mismatch** (root cause)
   - Variables `?p`, `?q` in formula string
   - Variables not recognized by Z3 parser
   - Mismatch between query variable names and SMT-LIB format

3. **Generation Issue** (underlying cause)
   - Data-4 variant specifically triggers this issue
   - Optimization algorithm generates incompatible formulas
   - Other data variants (data-1, data-2, data-3, data-5) do NOT have this issue

### Why Only Data-4?
- **data-1**: No exceptions (data-1 uses simpler constraints)
- **data-2**: No exceptions (Q2 completely succeeds)
- **data-3**: No exceptions (but has 7 timeouts instead)
- **data-4**: **451 exceptions** (68 unique node IDs causing all failures)
- **data-5**: No exceptions (has 7 timeouts instead)

Data-4 appears to hit a "sweet spot" where:
1. Constraints are complex enough to trigger optimization
2. Optimization generates formula patterns Z3 can't parse
3. Results in systematic parsing failures

## Next Steps for Root Cause Fix

### Step 1: Variable Registration Analysis
Need to verify in the C++ code:
- What variable names does `get_query_ctx().get_var_name(var)` return?
- Are they `?p`, `?q` or just `p`, `q`?
- How do they map to the formula string `?p == attr1 and ?q == attr2`?

### Step 2: Formula Generation Source  
Search for where cell constraints are constructed:
```bash
grep -r "cell {" src/ --include="*.cc" --include="*.h"
grep -r "?p ==" src/ --include="*.cc" --include="*.h"
```

### Step 3: Z3 Integration Points
Check how formulas are passed to Z3:
- `src/query/smt/smt_ctx.h` - Z3 context and parsing
- Look for: `parse_string()`, `add_real_var()`, declaration lists (`dels`)

### Step 4: Format Converter
Implement conversion between:
- Query variable format: `?p`, `?q`
- SMT-LIB format: Valid Z3 identifiers
- Test with: `p -> ?p` or `?p -> p` transformations

## Testing Strategy

### Test 1: Verify Fix
After fixing variable name mismatch, rerun all 68 error queries:
```bash
python3 test_error_queries.py
```
Expected: 68/68 success (100%)

### Test 2: No Regression
Ensure fix doesn't break other queries:
```bash
python3 evaluation/script/evaluation.py telecom --optimized
```
Expected: No new failures in data-1, data-2, data-3, data-5

### Test 3: Performance Impact
Check Z3 performance after formula fix:
- Measure: z3_solver_time, z3_operation_time
- Compare: Before/after overhead
- Acceptable: <5% slowdown

## Files Involved

### Error Query Extraction
- Generated: `/tmp/error_node_ids.txt` (68 node IDs)
- Test script: `test_error_queries.py`
- Results: All 68 queries consistently fail

### C++ Code to Investigate
1. `src/query/executor/binding_iter/paths/data_test/lra/bfs_enum.cc` (line 63)
   - Exception location
   - Variable registration
   
2. `src/query/smt/smt_ctx.h` (lines 216-229)
   - Z3 formula parsing interface
   
3. `src/network/server/session/http/http_quad_session.cc` (line 108)
   - Exception logging

### Build Artifacts
- Debug build: `build/Debug/` (contains symbols)
- Release build: `build/Release/` (faster execution)

## Debugging Evidence

### Error Pattern Consistency
- **Same formula, different nodes**: All 68 queries use identical formula
- **Deterministic failure**: 0% success rate on rerun
- **No timeout interference**: Pure parsing exceptions, not performance timeouts
- **Isolated to data-4**: Other variants unaffected

### Performance Context
Some error queries show high solver activity before failing:
```
z3_operation_time: 7.49838 ms (highest observed)
z3_solver_time: 1.67806 ms
exploration_depth: 93 (highest observed)
```

This suggests Z3 was actively working before hitting the parse error.

## Conclusion

The **68 error queries are 100% reproducible** and **all fail with the same exception**. This is NOT a random or transient issue—it's a systematic formula parsing problem specific to how the optimized algorithm generates constraints for the data-4 variant.

The fix likely involves normalizing variable names between the query layer (`?p`, `?q`) and the SMT-LIB layer that Z3 expects.
