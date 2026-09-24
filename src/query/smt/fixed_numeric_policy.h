#pragma once

#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>

namespace SMT {

// The bounded solvers deliberately use one explicit machine-numeric policy.
// These widths are not inferred from schema metadata.  Bounded results are
// hints only; correctness decisions are confirmed in the original theory.
struct FixedInt64Binary64Policy {
    static constexpr unsigned integer_bit_width = 64;
    static constexpr unsigned floating_point_exponent_bits = 11;
    static constexpr unsigned floating_point_significand_bits = 53;
};

// Return an SMT-LIB Real term denoting the exact mathematical value stored by
// a finite IEEE-754 binary64 database field.  A decimal round-trip string is
// sufficient to reconstruct the double, but is not generally the same Real
// number; the explicit dyadic rational keeps exact-theory validation sound.
inline std::string binary64_to_exact_real_literal(double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument("non-finite binary64 database value");
    }

    uint64_t bits = 0;
    static_assert(sizeof(bits) == sizeof(value));
    std::memcpy(&bits, &value, sizeof(bits));
    const bool negative = (bits >> 63U) != 0;
    const uint64_t exponent_bits = (bits >> 52U) & 0x7ffU;
    const uint64_t fraction = bits & ((uint64_t{1} << 52U) - 1U);
    if (exponent_bits == 0 && fraction == 0) {
        return "0";
    }

    const uint64_t significand = exponent_bits == 0
                               ? fraction
                               : (uint64_t{1} << 52U) | fraction;
    const int exponent = exponent_bits == 0
                       ? -1074
                       : static_cast<int>(exponent_bits) - 1023 - 52;
    std::string magnitude;
    if (exponent == 0) {
        magnitude = std::to_string(significand);
    } else if (exponent > 0) {
        magnitude = "(* " + std::to_string(significand)
                  + " (^ 2 " + std::to_string(exponent) + "))";
    } else {
        magnitude = "(/ " + std::to_string(significand)
                  + " (^ 2 " + std::to_string(-exponent) + "))";
    }
    return negative ? "(- " + magnitude + ")" : magnitude;
}

inline std::string substitute_binary64_registers(
        std::string formula,
        const std::map<std::string, double>& register_values) {
    for (const auto& [name, value] : register_values) {
        const auto replacement = binary64_to_exact_real_literal(value);
        std::size_t pos = 0;
        while ((pos = formula.find(name, pos)) != std::string::npos) {
            if (pos > 0) {
                const unsigned char previous = static_cast<unsigned char>(formula[pos - 1]);
                if (std::isalnum(previous) || previous == '_' || previous == '?') {
                    pos += name.size();
                    continue;
                }
            }
            const auto end = pos + name.size();
            if (end < formula.size()) {
                const unsigned char next = static_cast<unsigned char>(formula[end]);
                if (std::isalnum(next) || next == '_') {
                    pos = end;
                    continue;
                }
            }
            formula.replace(pos, name.size(), replacement);
            pos += replacement.size();
        }
    }
    return formula;
}

template<typename AttributeKey, typename Transition>
bool apply_finite_binary64_register_assignments(
        const std::map<std::tuple<std::string, AttributeKey>, double>& attributes,
        const Transition& transition,
        std::map<std::string, double>& registers) {
    auto updated = registers;
    for (const auto& [register_name, attribute_name] : transition.reg_assignments) {
        bool found = false;
        for (const auto& [key, value] : attributes) {
            if (std::get<0>(key) == attribute_name) {
                if (!std::isfinite(value)) return false;
                updated[register_name] = value;
                found = true;
                break;
            }
        }
        if (!found) return false;
    }
    registers = std::move(updated);
    return true;
}

} // namespace SMT
