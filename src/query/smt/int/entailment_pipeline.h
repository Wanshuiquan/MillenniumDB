#pragma once

#include <unordered_map>
#include <vector>

#include "z3++.h"
#include "query/smt/int/abstract_rewriter.h"
#include "query/smt/smt_ctx.h"

namespace SMT::Int {

enum class AtomDecision {
    Keep,
    Redundant,
    Inconsistent
};

class EntailmentPipeline64 {
public:
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

            if (!is_abstractable(atom_int) || collected_expr_bv.size() != collected_expr_int.size()) {
                if (!is_sat_with_extra(exact_solver, collected_expr_int, !atom_int)) {
                    return AtomDecision::Redundant;
                }
                if (!is_sat_with_extra(exact_solver, collected_expr_int, atom_int)) {
                    return AtomDecision::Inconsistent;
                }

                collected_expr_int.push_back(atom_int);
                return AtomDecision::Keep;
            }

            z3::expr atom_bv = AbstractRewriter64::rewrite_int_atom_to_bv(atom_int, bv_ctx, bv_vars);
            const bool full_abstract_cover = true;

            if (is_entailed(exact_solver, collected_expr_bv, collected_expr_int, atom_bv, atom_int, full_abstract_cover)) {
                return AtomDecision::Redundant;
            }

            if (!is_satisfiable(exact_solver, collected_expr_bv, collected_expr_int, atom_bv, atom_int, full_abstract_cover)) {
                return AtomDecision::Inconsistent;
            }

            collected_expr_bv.push_back(atom_bv);
            collected_expr_int.push_back(atom_int);
            return AtomDecision::Keep;
        });
    }

    bool check_sat_with_fallback(
            z3::solver& exact_solver,
            const std::vector<z3::expr>& collected_expr_bv,
            const std::vector<z3::expr>& collected_expr_int) const
    {
        return get_smt_ctx().time_int_entailment([&]() {
            if (collected_expr_int.empty()) {
                return true;
            }

            const bool full_abstract_cover =
                    !collected_expr_bv.empty() && collected_expr_bv.size() == collected_expr_int.size();

            if (full_abstract_cover && is_sat(bv_solver, collected_expr_bv)) {
                return true;
            }

            return is_sat(exact_solver, collected_expr_int);
        });
    }

private:
    z3::context bv_ctx;
    std::unordered_map<std::string, z3::expr> bv_vars;
    mutable z3::solver bv_solver = z3::solver(bv_ctx);

    static bool is_abstractable(const z3::expr& expr) {
        if (expr.is_true() || expr.is_false() || expr.is_numeral()) {
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
        case Z3_OP_IDIV:
        case Z3_OP_MOD:
            return true;
        default:
            return false;
        }
    }

    static bool is_sat(z3::solver& solver, const std::vector<z3::expr>& assumptions) {
        if (assumptions.empty()) {
            return true;
        }

        solver.push();
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        const bool sat = solver.check() == z3::sat;
        solver.pop();
        return sat;
    }

    static bool is_sat_with_extra(z3::solver& solver, const std::vector<z3::expr>& assumptions, const z3::expr& extra) {
        solver.push();
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        solver.add(extra);
        const bool sat = solver.check() == z3::sat;
        solver.pop();
        return sat;
    }

    bool is_entailed(
            z3::solver& exact_solver,
            const std::vector<z3::expr>& abstract_assumptions,
            const std::vector<z3::expr>& exact_assumptions,
            const z3::expr& abstract_atom,
            const z3::expr& exact_atom,
            bool full_abstract_cover)
    {
        if (full_abstract_cover && is_sat_with_extra(bv_solver, abstract_assumptions, !abstract_atom)) {
            return false;
        }

        return !is_sat_with_extra(exact_solver, exact_assumptions, !exact_atom);
    }

    bool is_satisfiable(
            z3::solver& exact_solver,
            const std::vector<z3::expr>& abstract_assumptions,
            const std::vector<z3::expr>& exact_assumptions,
            const z3::expr& abstract_atom,
            const z3::expr& exact_atom,
            bool full_abstract_cover)
    {
        if (full_abstract_cover && is_sat_with_extra(bv_solver, abstract_assumptions, abstract_atom)) {
            return true;
        }

        return is_sat_with_extra(exact_solver, exact_assumptions, exact_atom);
    }
};

} // namespace SMT::Int
