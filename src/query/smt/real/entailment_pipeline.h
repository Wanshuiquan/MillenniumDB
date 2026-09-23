#pragma once

#include <unordered_map>
#include <vector>

#include "z3++.h"
#include "query/smt/smt_ctx.h"
#include "query/smt/solver_check.h"

namespace SMT::Real {

enum class AtomDecision {
    Keep,
    Redundant,
    Inconsistent
};

class EntailmentPipeline {
public:
    explicit EntailmentPipeline(SMT::SolverCheck checker = {})
        : checker_(std::move(checker)) { }

    AtomDecision evaluate_and_update(
            std::vector<z3::expr>& collected_expr_bv,
            std::vector<z3::expr>& collected_expr_int,
            const z3::expr& atom_int)
    {
        return get_smt_ctx().time_real_entailment([&]() {
            collected_expr_bv.clear();
            if (atom_int.is_true()) {
                return AtomDecision::Redundant;
            }
            if (atom_int.is_false()) {
                return AtomDecision::Inconsistent;
            }

            const z3::expr& atom_real = atom_int;

            const auto counterexample = relation_status(collected_expr_int, !atom_real);
            if (counterexample == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (counterexample == SMT::CheckStatus::Unsat) {
                return AtomDecision::Redundant;
            }

            const auto consistent = relation_status(collected_expr_int, atom_real);
            if (consistent == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (consistent == SMT::CheckStatus::Unsat) {
                return AtomDecision::Inconsistent;
            }

            collected_expr_int.push_back(atom_int);
            return AtomDecision::Keep;
        });
    }

    SMT::CheckStatus check_sat_status(const std::vector<z3::expr>& assumptions) const {
        if (assumptions.empty()) return SMT::CheckStatus::Sat;
        z3::solver solver(assumptions.front().ctx());
        for (const auto& expression : assumptions) solver.add(expression);
        return checker_(solver);
    }

private:
    SMT::SolverCheck checker_;

    SMT::CheckStatus relation_status(const std::vector<z3::expr>& assumptions, const z3::expr& atom) const {
        z3::solver solver(atom.ctx());
        for (const auto& expr : assumptions) {
            solver.add(expr);
        }
        solver.add(atom);
        return checker_(solver);
    }
};

} // namespace SMT::Real
