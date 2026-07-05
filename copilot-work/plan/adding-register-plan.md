# Adding Register Variables to MQL Regular Expressions

## Goal
Extend MQL path constraints with register variables such as `??x`, `??y`, and `??z`, so regular expressions can carry memory across node and edge checks in data-constrained paths.

## Scope
- Add parser and AST support for register variables and register assignments inside data constraints.
- Extend the SMT path automaton so transitions can carry register updates.
- Update the path evaluation algorithms to maintain and instantiate register values during traversal.
- Add a dedicated MQL test suite for register semantics.

## Proposed Syntax
- Register variable names start with `??`, for example `??x`.
- Global parameters keep the existing `?x`, `?y`, `?z` form.
- `=` is reserved for register assignment.
- `==` is used for equality checks in data constraints.
- When a transition has both register updates and a data constraint, they are separated by `in`, for example:
  - `??x = age in age == ?start`
  - `??odd = weight, ??node = val in ??odd != ?threshold`
- When a transition only updates registers, it should contain only assignment expressions, for example:
  - `??x = age`
  - `??odd = weight, ??even = other_weight`
- When a transition has neither a register update nor a data constraint, it should remain `true`.
- Existing constraints without register assignments remain valid.

## Semantics To Implement
1. Register variables are scoped to a path evaluation and persist across transitions.
2. A transition may both:
   - check the current node or edge attributes, and
   - update one or more registers.
3. Register values become available immediately for subsequent transition evaluation.
4. Global parameters remain restricted to constant coefficients.
5. Register values may participate in products with database attributes, for example `age * ??r`.
6. Products that mix two runtime attributes remain invalid, for example `age * weight`.

## Implementation Plan

### 1. Grammar and Parsing
- Extend the MQL grammar to recognize identifiers prefixed with `??`.
- Distinguish register assignment `??r = attr` from boolean equality `lhs == rhs`.
- Update parser visitors so data constraints produce:
  - guard expressions, and
  - register update bindings.

### 2. Internal Representation
- Add a register-update field to `SMTTransition`.
- Represent each update as a mapping from register variable to the attribute or expression assigned on that transition.
- Preserve backward compatibility for transitions that do not update registers.

### 3. Expression and Type Rules
- Extend expression analysis to classify register references separately from global parameters and database attributes.
- Enforce the syntax split between update expressions and boolean constraints:
  - updates use `=`
  - predicates use `==`, `!=`, `<`, `<=`, `>`, `>=`, etc.
  - mixed update/check clauses use `updates in predicate`
- Reject unsupported products such as attribute-by-attribute and register-by-property combinations where the task note says they are not allowed.
- Decide and document how mixed arithmetic typing behaves for integer vs non-integer register paths.

### 4. Automaton Construction
- Ensure MQL path parsing passes register updates into `SMTAutomaton`.
- Keep determinization and transition rewrites stable when labels now include:
  - edge type,
  - property check formula,
  - direction,
  - register update payload.
- Revisit any transition equality or deduplication logic so updates are part of the label identity.

### 5. Evaluation Algorithm
- Extend path search state to carry current register bindings.
- On each transition:
  - bind the current node or edge attributes,
  - apply register updates,
  - instantiate register references,
  - evaluate the resulting guard.
- Make sure visited-state keys include register memory when correctness depends on it.

### 6. Validation
- Add a new MQL suite `tests/mql/test_suites/registers`.
- Cover at least:
  - all values different than the first one,
  - increasing values in edges and nodes,
  - alternating odd/even edge classes with stable remembered values,
  - interactions that mix global parameters and registers in the same path.
- After implementation, remove the temporary ignore entries and run `./scripts/run-tests mql`.

## Test Scaffolding Added Now
- A new `registers` MQL suite is added with three representative fixtures.
- Two extra fixtures are included to exercise mixed parameter/register behavior.
- Because register syntax is not implemented yet, the new cases are registered in the test runner but temporarily ignored.
- Once parser and evaluator support lands, the ignore list should be removed and the suite should become active.

## Open Questions
- Should register assignments inside one constraint be visible to the rest of that same constraint, or only to later transitions?
- Do we want a separate `DATA_TEST` variant for register-enabled execution, or should the existing variants absorb the feature?
- How should registers be serialized or printed in automaton debugging output?
