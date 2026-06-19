## Debugging the "expression is not a string literal" Exception

### Root Cause Analysis

**Problem:** Z3 SMT solver is rejecting formulas during evaluation of cell constraints in DATA_TEST queries.

**Exception Location:** 
- File: `src/query/executor/binding_iter/paths/data_test/lra/bfs_enum.cc`, line 63
- Call: `auto property = get_smt_ctx().parse(formula);`

**Issue Details:**
1. The optimization algorithm generates cell constraints with query variables:
   - Pattern: `(cell {?p == attr1 and ?q == attr2})`
   - Variables: `?p`, `?q` (query variable format)
   - Attributes: `attr1`, `attr2`

2. When `eval_check()` is called with this formula string, the function:
   - Registers SMT variables with: `add_real_var(name)`
   - Then tries to parse: `context.parse_string(formula.c_str(), sort, dels)[0]`

3. Z3 rejects the formula because:
   - The query variable names (`?p`, `?q`) are not in SMT-LIB format
   - Z3 expects either properly declared variables or string literals
   - The formula might contain variable references that aren't in the `dels` vector

### Key Code Path:
```
eval_check(uint64_t obj, MacroState& macroState, const std::string& formula)
  ├─ For each variable: add_real_var(get_query_ctx().get_var_name(var))
  ├─ Parse formula: context.parse_string(formula.c_str(), sort, dels)
  └─ FAILS HERE: Z3 cannot parse formula with improper variable names
```

### Potential Solutions:

**Option 1: Normalize variable names before parsing**
- Convert `?p` to `p` in the formula string before passing to Z3
- Ensure all variables are properly registered in `dels` vector

**Option 2: Convert formula to proper SMT-LIB format**
- Build formula incrementally using Z3 API instead of string parsing
- Manually construct z3::expr objects for each constraint

**Option 3: Add formula string validation/preprocessing**
- Log the actual formula string being parsed
- Add error handling with better error messages
- Provide feedback on which variables failed to parse

### Debugging Strategy:
1. Add logging to `eval_check()` to see the actual formula strings being parsed
2. Check variable names in `vars` map
3. Compare `get_query_ctx().get_var_name(var)` output with names in formula
4. Trace through the optimization algorithm to understand formula construction

### Recommended Next Steps:
1. Add debug output to see actual formula strings when they fail
2. Implement formula preprocessing to normalize variable names
3. Add validation to ensure all variables in formula are properly registered
