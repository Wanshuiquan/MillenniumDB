#pragma once

#include <unordered_map>
#include <optional>
#include <vector>

#include "z3++.h"
#include "query/smt/int/abstract_rewriter.h"
#include "query/smt/smt_ctx.h"
#include "query/smt/solver_check.h"

namespace SMT::Int {

enum class AtomDecision {
    Keep,
    Redundant,
    Inconsistent
};

class EntailmentPipeline64 {
public:
    explicit EntailmentPipeline64(
            SMT::SolverCheck exact_check = {},
            SMT::SolverCheck bounded_check = {})
        : exact_check_(std::move(exact_check)),
          bounded_check_(std::move(bounded_check)) { }

    AtomDecision evaluate_and_update(
            z3::solver& exact_solver,
            std::vector<z3::expr>& collected_expr_bv,
            std::vector<z3::expr>& collected_expr_int,
            const z3::expr& atom_int)
    {
        return get_smt_ctx().time_int_entailment([&]() {
            if (atom_int.is_true()) {
                return AtomDecision::Redundant;
            }
            if (atom_int.is_false()) {
                return AtomDecision::Inconsistent;
            }

            bool abstractable = !bounded_disabled_ && is_abstractable(atom_int)
                    && collected_expr_bv.size() == collected_expr_int.size();
            std::optional<z3::expr> bounded_atom;
            if (abstractable) {
                try {
                    bounded_atom.emplace(AbstractRewriter64::rewrite_int_atom_to_bv(
                            atom_int, bv_ctx, bv_vars));
                    // Always run the bounded query as a hint, including the UNSAT
                    // case, but never derive a semantic decision from it.
                    (void)check_with_extra(
                            bv_solver, collected_expr_bv, *bounded_atom, bounded_check_);
                } catch (...) {
                    // A hint must be observationally irrelevant.  Disable it
                    // permanently after any partial rewrite/check failure.
                    bounded_disabled_ = true;
                    abstractable = false;
                    bounded_atom.reset();
                    collected_expr_bv.clear();
                }
            }
            const auto counterexample = check_with_extra(
                    exact_solver, collected_expr_int, !atom_int, exact_check_);
            if (counterexample == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (counterexample == SMT::CheckStatus::Unsat) {
                return AtomDecision::Redundant;
            }
            const auto consistent = check_with_extra(
                    exact_solver, collected_expr_int, atom_int, exact_check_);
            if (consistent == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (consistent == SMT::CheckStatus::Unsat) {
                return AtomDecision::Inconsistent;
            }
            if (abstractable) {
                collected_expr_bv.push_back(*bounded_atom);
            } else {
                collected_expr_bv.clear();
            }
            collected_expr_int.push_back(atom_int);
            return AtomDecision::Keep;
        });
    }

    SMT::CheckStatus check_sat_status(
            z3::solver& exact_solver,
            const std::vector<z3::expr>&,
            const std::vector<z3::expr>& collected_expr_int) const
    {
        return get_smt_ctx().time_int_entailment([&]() {
            return check(exact_solver, collected_expr_int, exact_check_);
        });
    }

private:
    z3::context bv_ctx;
    std::unordered_map<std::string, z3::expr> bv_vars;
    mutable z3::solver bv_solver = z3::solver(bv_ctx);
    SMT::SolverCheck exact_check_;
    SMT::SolverCheck bounded_check_;
    bool bounded_disabled_ = false;

    static bool is_abstractable(const z3::expr& expr) {
        if (expr.is_numeral()) {
            int64_t ignored = 0;
            return !expr.is_int() || expr.is_numeral_i64(ignored);
        }
        if (expr.is_true() || expr.is_false()) {
            return true;
        }
        if (expr.is_const()) {
            return expr.is_bool() || expr.is_int();
        }

        for (unsigned i = 0; i < expr.num_args(); ++i) {
            if (!is_abstractable(expr.arg(i))) {
                return false;
            }
        }

        switch (expr.decl().decl_kind()) {
        case Z3_OP_NOT:
        case Z3_OP_AND:
        case Z3_OP_OR:
        case Z3_OP_IMPLIES:
        case Z3_OP_ITE:
        case Z3_OP_EQ:
        case Z3_OP_DISTINCT:
        case Z3_OP_LE:
        case Z3_OP_LT:
        case Z3_OP_GE:
        case Z3_OP_GT:
        case Z3_OP_UMINUS:
        case Z3_OP_ADD:
        case Z3_OP_SUB:
        case Z3_OP_MUL:
            return true;
        // Int div/mod and signed bit-vector div/rem differ on negative
        // operands and exceptional machine values.  Keep them exact.
        default:
            return false;
        }
    }

    static SMT::CheckStatus check(
            z3::solver& solver,
            const std::vector<z3::expr>& assumptions,
            const SMT::SolverCheck& checker) {
        solver.push();
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        const auto result = checker(solver);
        solver.pop();
        return result;
    }

    static SMT::CheckStatus check_with_extra(
            z3::solver& solver,
            const std::vector<z3::expr>& assumptions,
            const z3::expr& extra,
            const SMT::SolverCheck& checker) {
        solver.push();
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        solver.add(extra);
        const auto result = checker(solver);
        solver.pop();
        return result;
    }
};

} // namespace SMT::Int
