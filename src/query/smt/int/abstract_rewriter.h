#pragma once

#include <cstdint>
#include <regex>
#include <stdexcept>
#include <string>
#include <unordered_map>

#include "z3++.h"
#include "query/smt/fixed_numeric_policy.h"

namespace SMT::Int {

class AbstractRewriter64 {
public:
    static constexpr unsigned BIT_WIDTH = SMT::FixedInt64Binary64Policy::integer_bit_width;

    static std::string rewrite_lra_formula_to_int(std::string formula) {
        // DATA_TEST constraints are generated with a real epsilon trick for strict bounds.
        // For integer semantics, replacing epsilon with 1 preserves strictness.
        formula = std::regex_replace(formula, std::regex("\\(\\+\\s+epsilon\\s+"), "(+ 1 ");
        // Normalize integer-looking decimal literals (e.g. 5.000000 -> 5).
        formula = std::regex_replace(formula, std::regex("(-?[0-9]+)\\.0+"), "$1");
        return formula;
    }

    static z3::expr rewrite_int_atom_to_bv(
            const z3::expr& expr,
            z3::context& bv_ctx,
            std::unordered_map<std::string, z3::expr>& bv_vars)
    {
        if (expr.is_bool()) {
            return rewrite_bool(expr, bv_ctx, bv_vars);
        }
        return rewrite_int_term(expr, bv_ctx, bv_vars);
    }

private:
    static z3::expr get_or_create_bv_var(
            const std::string& name,
            z3::context& bv_ctx,
            std::unordered_map<std::string, z3::expr>& bv_vars)
    {
        auto it = bv_vars.find(name);
        if (it != bv_vars.end()) {
            return it->second;
        }
        auto inserted = bv_vars.emplace(name, bv_ctx.bv_const(name.c_str(), BIT_WIDTH));
        return inserted.first->second;
    }

    static z3::expr int64_to_bv(int64_t value, z3::context& bv_ctx) {
        return bv_ctx.bv_val(static_cast<uint64_t>(value), BIT_WIDTH);
    }

    static z3::expr rewrite_int_term(
            const z3::expr& expr,
            z3::context& bv_ctx,
            std::unordered_map<std::string, z3::expr>& bv_vars)
    {
        if (expr.is_numeral()) {
            int64_t val = 0;
            if (expr.is_int() && expr.is_numeral_i64(val)) {
                return int64_to_bv(val, bv_ctx);
            }
            throw std::invalid_argument("integer numeral does not fit the fixed int64 policy");
        }

        if (expr.is_const()) {
            return get_or_create_bv_var(expr.to_string(), bv_ctx, bv_vars);
        }

        const auto op = expr.decl().decl_kind();
        switch (op) {
        case Z3_OP_ITE:
            return z3::ite(
                    rewrite_bool(expr.arg(0), bv_ctx, bv_vars),
                    rewrite_int_term(expr.arg(1), bv_ctx, bv_vars),
                    rewrite_int_term(expr.arg(2), bv_ctx, bv_vars));
        case Z3_OP_UMINUS:
            return -rewrite_int_term(expr.arg(0), bv_ctx, bv_vars);
        case Z3_OP_ADD: {
            auto value = rewrite_int_term(expr.arg(0), bv_ctx, bv_vars);
            for (unsigned i = 1; i < expr.num_args(); ++i) {
                value = value + rewrite_int_term(expr.arg(i), bv_ctx, bv_vars);
            }
            return value;
        }
        case Z3_OP_SUB: {
            auto value = rewrite_int_term(expr.arg(0), bv_ctx, bv_vars);
            for (unsigned i = 1; i < expr.num_args(); ++i) {
                value = value - rewrite_int_term(expr.arg(i), bv_ctx, bv_vars);
            }
            return value;
        }
        case Z3_OP_MUL: {
            auto value = rewrite_int_term(expr.arg(0), bv_ctx, bv_vars);
            for (unsigned i = 1; i < expr.num_args(); ++i) {
                value = value * rewrite_int_term(expr.arg(i), bv_ctx, bv_vars);
            }
            return value;
        }
        case Z3_OP_IDIV: {
            auto value = rewrite_int_term(expr.arg(0), bv_ctx, bv_vars);
            for (unsigned i = 1; i < expr.num_args(); ++i) {
                const auto divisor = rewrite_int_term(expr.arg(i), bv_ctx, bv_vars);
                const auto quotient = value / divisor;
                const auto remainder = z3::srem(value, divisor);
                const auto zero = bv_ctx.bv_val(0, BIT_WIDTH);
                const auto signs_differ = (value < zero) != (divisor < zero);
                value = z3::ite(remainder != zero && signs_differ,
                                quotient - bv_ctx.bv_val(1, BIT_WIDTH),
                                quotient);
            }
            return value;
        }
        case Z3_OP_MOD: {
            const auto dividend = rewrite_int_term(expr.arg(0), bv_ctx, bv_vars);
            const auto divisor = rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
            const auto remainder = z3::srem(dividend, divisor);
            const auto zero = bv_ctx.bv_val(0, BIT_WIDTH);
            const auto signs_differ = (dividend < zero) != (divisor < zero);
            return z3::ite(remainder != zero && signs_differ,
                           remainder + divisor,
                           remainder);
        }
        default:
            throw std::invalid_argument("unsupported integer term in fixed int64 rewrite");
        }
    }

    static z3::expr rewrite_bool(
            const z3::expr& expr,
            z3::context& bv_ctx,
            std::unordered_map<std::string, z3::expr>& bv_vars)
    {
        if (expr.is_true()) {
            return bv_ctx.bool_val(true);
        }
        if (expr.is_false()) {
            return bv_ctx.bool_val(false);
        }
        if (expr.is_const() && expr.is_bool()) {
            return bv_ctx.bool_const(expr.to_string().c_str());
        }

        const auto op = expr.decl().decl_kind();
        switch (op) {
        case Z3_OP_NOT:
            return !rewrite_bool(expr.arg(0), bv_ctx, bv_vars);
        case Z3_OP_AND: {
            auto value = rewrite_bool(expr.arg(0), bv_ctx, bv_vars);
            for (unsigned i = 1; i < expr.num_args(); ++i) {
                value = value && rewrite_bool(expr.arg(i), bv_ctx, bv_vars);
            }
            return value;
        }
        case Z3_OP_OR: {
            auto value = rewrite_bool(expr.arg(0), bv_ctx, bv_vars);
            for (unsigned i = 1; i < expr.num_args(); ++i) {
                value = value || rewrite_bool(expr.arg(i), bv_ctx, bv_vars);
            }
            return value;
        }
        case Z3_OP_IMPLIES:
            return z3::implies(
                    rewrite_bool(expr.arg(0), bv_ctx, bv_vars),
                    rewrite_bool(expr.arg(1), bv_ctx, bv_vars));
        case Z3_OP_ITE:
            return z3::ite(
                    rewrite_bool(expr.arg(0), bv_ctx, bv_vars),
                    rewrite_bool(expr.arg(1), bv_ctx, bv_vars),
                    rewrite_bool(expr.arg(2), bv_ctx, bv_vars));
        case Z3_OP_EQ:
            if (expr.arg(0).is_bool()) {
                return rewrite_bool(expr.arg(0), bv_ctx, bv_vars)
                       == rewrite_bool(expr.arg(1), bv_ctx, bv_vars);
            }
            return rewrite_int_term(expr.arg(0), bv_ctx, bv_vars)
                   == rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
        case Z3_OP_DISTINCT:
            if (expr.num_args() == 2) {
                if (expr.arg(0).is_bool()) {
                    return rewrite_bool(expr.arg(0), bv_ctx, bv_vars)
                           != rewrite_bool(expr.arg(1), bv_ctx, bv_vars);
                }
                return rewrite_int_term(expr.arg(0), bv_ctx, bv_vars)
                       != rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
            } else {
                z3::expr_vector distinct_terms(bv_ctx);
                for (unsigned i = 0; i < expr.num_args(); ++i) {
                    if (expr.arg(i).is_bool()) {
                        distinct_terms.push_back(rewrite_bool(expr.arg(i), bv_ctx, bv_vars));
                    } else {
                        distinct_terms.push_back(rewrite_int_term(expr.arg(i), bv_ctx, bv_vars));
                    }
                }
                return z3::distinct(distinct_terms);
            }
        case Z3_OP_LE:
            return rewrite_int_term(expr.arg(0), bv_ctx, bv_vars)
                   <= rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
        case Z3_OP_LT:
            return rewrite_int_term(expr.arg(0), bv_ctx, bv_vars)
                   < rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
        case Z3_OP_GE:
            return rewrite_int_term(expr.arg(0), bv_ctx, bv_vars)
                   >= rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
        case Z3_OP_GT:
            return rewrite_int_term(expr.arg(0), bv_ctx, bv_vars)
                   > rewrite_int_term(expr.arg(1), bv_ctx, bv_vars);
        default:
            throw std::invalid_argument("unsupported Boolean term in fixed int64 rewrite");
        }
    }
};

} // namespace SMT::Int
