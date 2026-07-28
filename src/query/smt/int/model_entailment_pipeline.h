#pragma once

#include <unordered_map>
#include <vector>

#include "z3++.h"

namespace SMT::Int {

enum class ModelAtomDecision {
    Keep,
    Redundant,
    Inconsistent
};

class EntailmentPipeline {
public:
    ModelAtomDecision evaluate_and_update(
            std::vector<z3::expr>& collected_expr_bv,
            std::vector<z3::expr>& collected_expr_int,
            const z3::expr& atom_int)
    {
        if (atom_int.is_true()) {
            return ModelAtomDecision::Redundant;
        }
        if (atom_int.is_false()) {
            return ModelAtomDecision::Inconsistent;
        }

        const z3::expr& atom_real = atom_int;

        // Pipeline order: bitvector entailment first, then integer entailment.
        if (is_entailed(collected_expr_int, atom_real)) {
            return ModelAtomDecision::Redundant;
        }

        if (is_inconsistent(collected_expr_int, atom_real)) {
            return ModelAtomDecision::Inconsistent;
        }

        collected_expr_int.push_back(atom_int);
        return ModelAtomDecision::Keep;
    }

private:

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
