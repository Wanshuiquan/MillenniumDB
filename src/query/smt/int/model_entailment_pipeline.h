#pragma once

#include <unordered_map>
#include <vector>

#include "query/smt/int/entailment_pipeline.h"

namespace SMT::Int {

class ExactEntailmentPipeline {
public:
    explicit ExactEntailmentPipeline(SMT::SolverCheck checker = {})
        : checker_(std::move(checker)) { }

    AtomDecision evaluate_and_update(
            z3::solver& exact_solver,
            std::vector<z3::expr>& collected_expr_bv,
            std::vector<z3::expr>& collected_expr_int,
            const z3::expr& atom_int)
    {
        return get_smt_ctx().time_int_model_entailment([&]() {
            if (atom_int.is_true()) {
                return AtomDecision::Redundant;
            }
            if (atom_int.is_false()) {
                return AtomDecision::Inconsistent;
            }

            const auto counterexample = check_with_extra(
                    exact_solver, collected_expr_int, !atom_int);
            if (counterexample == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (counterexample == SMT::CheckStatus::Unsat) {
                return AtomDecision::Redundant;
            }
            const auto consistent = check_with_extra(
                    exact_solver, collected_expr_int, atom_int);
            if (consistent == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (consistent == SMT::CheckStatus::Unsat) {
                return AtomDecision::Inconsistent;
            }
            // Exact baseline never populates the bounded representation.
            collected_expr_bv.clear();
            collected_expr_int.push_back(atom_int);
            return AtomDecision::Keep;
        });
    }

    SMT::CheckStatus check_sat_status(
            z3::solver& solver,
            const std::vector<z3::expr>&,
            const std::vector<z3::expr>& exact) const
    {
        solver.push();
        for (const auto& expression : exact) solver.add(expression);
        const auto result = checker_(solver);
        solver.pop();
        return result;
    }

private:
    SMT::SolverCheck checker_;

    SMT::CheckStatus check_with_extra(
            z3::solver& solver,
            const std::vector<z3::expr>& assumptions,
            const z3::expr& extra) const {
        solver.push();
        for (const auto& expr : assumptions) solver.add(expr);
        solver.add(extra);
        const auto result = checker_(solver);
        solver.pop();
        return result;
    }
};

} // namespace SMT::Int
