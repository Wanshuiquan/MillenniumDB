#pragma once

#include <unordered_map>
#include <vector>

#include "z3++.h"
#include "query/smt/int/abstract_rewriter.h"

namespace SMT::Int {

enum class AtomDecision {
    Keep,
    Redundant,
    Inconsistent
};

class EntailmentPipeline64 {
public:
    AtomDecision evaluate_and_update(
            std::vector<z3::expr>& collected_expr_bv,
            std::vector<z3::expr>& collected_expr_int,
            const z3::expr& atom_int)
    {
        if (atom_int.is_true()) {
            return AtomDecision::Redundant;
        }
        if (atom_int.is_false()) {
            return AtomDecision::Inconsistent;
        }

        z3::expr atom_bv = AbstractRewriter64::rewrite_int_atom_to_bv(atom_int, bv_ctx, bv_vars);

        // Pipeline order: bitvector entailment first, then integer entailment.
        if (is_entailed(collected_expr_bv, atom_bv) || is_entailed(collected_expr_int, atom_int)) {
            return AtomDecision::Redundant;
        }

        if (is_inconsistent(collected_expr_bv, atom_bv) || is_inconsistent(collected_expr_int, atom_int)) {
            return AtomDecision::Inconsistent;
        }

        collected_expr_bv.push_back(atom_bv);
        collected_expr_int.push_back(atom_int);
        return AtomDecision::Keep;
    }

private:
    z3::context bv_ctx;
    std::unordered_map<std::string, z3::expr> bv_vars;

    static bool is_entailed(const std::vector<z3::expr>& assumptions, const z3::expr& atom) {
        z3::solver solver(atom.ctx());
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        solver.add(!atom);
        return solver.check() == z3::unsat;
    }

    static bool is_inconsistent(const std::vector<z3::expr>& assumptions, const z3::expr& atom) {
        z3::solver solver(atom.ctx());
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        solver.add(atom);
        return solver.check() == z3::unsat;
    }
};

} // namespace SMT::Int
