#pragma once

namespace SMT {

// The bounded solvers deliberately use one explicit machine-numeric policy.
// These widths are not inferred from schema metadata.  Bounded results are
// hints only; correctness decisions are confirmed in the original theory.
struct FixedInt64Binary64Policy {
    static constexpr unsigned integer_bit_width = 64;
    static constexpr unsigned floating_point_exponent_bits = 11;
    static constexpr unsigned floating_point_significand_bits = 53;
};

} // namespace SMT
