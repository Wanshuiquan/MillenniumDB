#pragma once

#include <unordered_map>
#include <vector>

#include "z3++.h"
#include "query/smt/smt_ctx.h"

namespace SMT::Real {

enum class AtomDecision {
    Keep,
    Redundant,
    Inconsistent
};

class EntailmentPipeline {
public:
    AtomDecision evaluate_and_update(
            std::vector<z3::expr>& collected_expr_bv,
            std::vector<z3::expr>& collected_expr_int,
            const z3::expr& atom_int)
    {
        return get_smt_ctx().time_real_entailment([&]() {
            if (atom_int.is_true()) {
                return AtomDecision::Redundant;
            }
            if (atom_int.is_false()) {
                return AtomDecision::Inconsistent;
            }

            const z3::expr& atom_real = atom_int;

            if (is_entailed(collected_expr_int, atom_real)) {
                return AtomDecision::Redundant;
            }

            if (is_inconsistent(collected_expr_int, atom_real)) {
                return AtomDecision::Inconsistent;
            }

            collected_expr_int.push_back(atom_int);
            return AtomDecision::Keep;
        });
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

} // namespace SMT::Real
