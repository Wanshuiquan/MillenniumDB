#pragma once

#include <list>
#include <utility>
#include <vector>

#include "query/executor/binding_iter/paths/data_test/search_state.h"
#include "query/smt/solver_check.h"

namespace Paths::DataTest {

// Stores a semantic antichain for every structural product-state key.  A state
// with weaker constraints subsumes a state with stronger constraints.  Solver
// UNKNOWN means the current exploration cannot soundly maintain its visited
// antichain and is therefore propagated as an exploration failure.
template<typename State>
class MacroStateAntichain {
public:
    using container_type = std::list<State>;
    using iterator = typename container_type::iterator;

    explicit MacroStateAntichain(SMT::SolverCheck checker = {}) : checker_(std::move(checker)) { }

    std::pair<iterator, bool> emplace(const State& candidate) {
        std::vector<iterator> subsumed_by_candidate;
        for (auto it = states_.begin(); it != states_.end(); ++it) {
            if (!same_structural_key(*it, candidate)) {
                continue;
            }

            // existing is weaker iff candidate => existing
            const auto candidate_implies_existing = implies(
                    candidate.semantic_constraints(),
                    it->semantic_constraints());
            if (candidate_implies_existing == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (candidate_implies_existing == SMT::CheckStatus::Unsat) {
                return {it, false};
            }

            // candidate is weaker iff existing => candidate
            const auto existing_implies_candidate = implies(
                    it->semantic_constraints(),
                    candidate.semantic_constraints());
            if (existing_implies_candidate == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (existing_implies_candidate == SMT::CheckStatus::Unsat) {
                subsumed_by_candidate.push_back(it);
            }
        }

        // Mutate only after every implication query has completed, so UNKNOWN
        // leaves the antichain exactly as it was before the attempted insert.
        for (const auto& it : subsumed_by_candidate) {
            states_.erase(it);
        }

        states_.push_back(candidate);
        auto inserted = states_.end();
        --inserted;
        return {inserted, true};
    }

    void clear() { states_.clear(); }
    std::size_t size() const { return states_.size(); }

private:
    container_type states_;
    SMT::SolverCheck checker_;

    static bool same_structural_key(const State& left, const State& right) {
        return left.automaton_state == right.automaton_state
            && left.path_state->node_id == right.path_state->node_id
            && left.reg_vals == right.reg_vals;
    }

    SMT::CheckStatus implies(
            const std::vector<z3::expr>& antecedent,
            const std::vector<z3::expr>& consequent) const
    {
        if (consequent.empty()) {
            return SMT::CheckStatus::Unsat;
        }
        z3::context& context = consequent.front().ctx();
        z3::solver solver(context);
        for (const auto& expression : antecedent) {
            solver.add(expression);
        }
        z3::expr_vector negated(context);
        for (const auto& expression : consequent) {
            negated.push_back(expression);
        }
        solver.add(!z3::mk_and(negated));
        return checker_(solver);
    }
};

template<typename InsertResult>
const PathState* surviving_path(const InsertResult& insertion) {
    return insertion.first->path_state;
}

} // namespace Paths::DataTest
