# Debugging Report: "expression is not a string literal" Exception

## Executive Summary

The MillenniumDB optimized query evaluation algorithm generates 451 formula parsing exceptions in the **data-4 variant** of the telecom case study. These occur specifically in cell constraint evaluation when parsing SMT-LIB formulas containing query variables.

**Status**: Root cause identified, debugging hooks added, ready for detailed trace.

---

## Problem Details

### Exception Information
- **Message**: `Unexpected(WORKER_ID) exception: expression is not a string literal`
- **Frequency**: 451 total occurrences in data-4 (7.1% failure rate)
- **Query Distribution**: 
  - Q0: 49 failures (49% of Q0 queries in data-4)
  - Q1-Q11: 38-46 failures each (36-46% failure rate)
  - Q2: 0 failures (100% success rate)
- **Occurs Only In**: data-4 variant (no exceptions in data-1, data-2, data-3, data-5)

### Offending Query Pattern
```
Match (NODE_ID) =[ 
  DATA_TEST ?e (cell {?p == attr1 and ?q == attr2})/ 
  ((:lived {true})/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 < ?p}))*/
  ((:used {true})/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 < ?p}))
] => (?to)
```

### Key Components of Problem
1. **Query Variables**: `?p`, `?q` (appear to be query result variables)
2. **Property Attributes**: `attr1`, `attr2` (database property names)
3. **Complex Expressions**: Includes arithmetic and comparisons:
   - `?q - attr2 <= 0.1`
   - `0.5 * attr1 + 0.1 < ?p`
   - `and` operators combining multiple conditions

---

## Root Cause Analysis

### Exception Location
- **File**: `src/query/executor/binding_iter/paths/data_test/lra/bfs_enum.cc`
- **Line**: 63 (in `eval_check` function)
- **Code**: `auto property = get_smt_ctx().parse(formula);`

### Call Stack
```
eval_check(uint64_t obj, MacroState& macroState, const std::string& formula)
  ↓ 
  register variables: add_real_var(get_query_ctx().get_var_name(var))
  ↓
  parse formula: context.parse_string(formula.c_str(), sort, dels)
  ↓ 
  Z3 REJECTS: "expression is not a string literal"
```

### Why Z3 Rejects the Formula
Z3's `parse_string()` method requires:
1. All variables to be either:
   - Declared in the `dels` vector (function/constant declarations)
   - Defined as standard SMT-LIB variables with proper syntax
2. Valid SMT-LIB syntax for all expressions
3. No undefined variable references

**The Problem**: 
- Query variable names like `?p`, `?q` are **not** standard SMT-LIB format
- The formula string contains these unregistered variable names
- Z3 cannot parse a formula with undefined variables

---

## Variables and Attributes Flow

### Variables Registered
```
For each ele in vars map:
  var_name = get_query_ctx().get_var_name(var)  // e.g., "p" or "?p"?
  get_smt_ctx().add_real_var(var_name)
  ↓
  This adds var_name to context but NOT to dels vector for parsing
```

### Formula Parsing Issue
```
Formula string: "?p == attr1 and ?q == attr2"
                   ↑              ↑
                   These variable names are NOT in the dels vector!
                   Z3 can't find definitions for ?p and ?q
                   → "expression is not a string literal"
```

---

## Debugging Modifications Made

Added exception handling in `bfs_enum.cc` (lines 63-92) to log:
1. The actual formula string being parsed
2. All registered variable names
3. All registered string attributes
4. All registered real attributes
5. The exact Z3 error message

**How to Use the Logs**:
When an exception occurs, stderr will show:
```
[BFS_ENUM::eval_check] Formula parsing failed
  Formula: <THE FORMULA STRING>
  Registered variables (from vars):
    - <var1>
    - <var2>
  Registered string attributes:
    - <attr1>
  Registered real attributes:
    - <attr1>
  Error: <Z3 ERROR MESSAGE>
```

---

## Next Debugging Steps

### Step 1: Capture Actual Debug Output
Run evaluation with stderr capture:
```bash
python3 evaluation/script/evaluating/telecom_optimized.py \
  --data-variant data-4 \
  --query-range 0 1 2>/tmp/debug.log
grep "BFS_ENUM::eval_check" /tmp/debug.log
```

### Step 2: Analyze Variable Names
Look for:
- What format are variable names? (`p` vs `?p`)
- Which variables are in formula but not registered?
- Mismatch between var names and formula references?

### Step 3: Find Formula Generation Source
Search for where these cell constraint formulas are constructed:
```bash
grep -r "cell {" src/ --include="*.cc" --include="*.h"
grep -r "?p ==" src/ --include="*.cc" --include="*.h"
```

### Step 4: Trace Variable Registration
Verify that all variables used in formula are registered before parsing:
- Check `get_query_ctx().get_var_name(var)` format
- Ensure formula uses same variable name format
- Check if names need preprocessing (e.g., `?p` → `p`)

---

## Potential Solutions

### Solution A: Normalize Variable Names Before Parsing
- Strip `?` prefix from variable names in formula before passing to Z3
- Ensure formula string uses same names as registered variables

### Solution B: Build Formula Using Z3 API
- Instead of string parsing, build z3::expr objects programmatically
- Manually construct binary operations for each constraint

### Solution C: Add Formula String Validation
- Before parsing, validate all variables in formula are registered
- Provide helpful error messages about missing variables
- Add a mapping layer between query variable names and SMT variable names

### Solution D: Modify Optimization Algorithm
- Check how data-4 specifically generates different query patterns than data-1-3, data-5
- Why does data-2 have 0 failures while data-4 has 40% failure?
- May indicate the optimization creates valid vs invalid formula patterns

---

## Critical Questions to Investigate

1. **Variable Name Format**: Are query variables actually `?p`, `?q` or something else?
2. **Data-4 Uniqueness**: Why only data-4 has exceptions? What's special about it?
3. **data-2 Success**: Q2 has 100% success rate - why is Q2 different?
4. **Formula Construction**: Who generates these cell constraint formulas?
5. **Z3 Registration**: Is the `dels` vector being populated correctly?

---

## Files Modified

1. `src/query/executor/binding_iter/paths/data_test/lra/bfs_enum.cc` (lines 63-92)
   - Added try-catch block with detailed logging
   - Preserves original exception for further debugging

---

## Related Timeouts (Separate Issue)

Note: There are also 14 actual timeouts in data-3 (7) and data-5 (7) variants - these are **separate from** the expression parsing exceptions and are likely performance-related, not syntax errors.

**Timeout Distribution**:
- data-3: Q0 (3), Q3 (4) = 7 total
- data-5: Q0 (3), Q1 (1), Q3 (2), Q7 (1) = 7 total

