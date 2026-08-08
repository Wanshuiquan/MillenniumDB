#pragma once

#include <functional>
#include <ostream>
#include <cstdint>
#include <tuple>
#include <string>

#include <utility>
#include <vector>
#include <map>
#include "graph_models/object_id.h"
#include "query/smt/smt_expr/smt_exprs.h"
#include "query/smt/smt_ctx.h"
#include "query/executor/binding_iter/paths/data_test/search_state.h"
namespace Paths::DataTest::RealModel {



   // Macro State to store the formulas
    struct MacroStateReal {
        const PathState* path_state;
        uint32_t automaton_state;
        std::vector<z3::expr> collected_expr_int;
        std::vector<z3::expr> collected_expr_bv;
        std::map<std::string, int64_t> reg_vals;
        mutable DfsIteratorState dfs_iter;
        uint_fast32_t dfs_transition = 0;

        void initialize_from(const MacroStateReal& other) {
            path_state = other.path_state;
            automaton_state = other.automaton_state;
            collected_expr_int = other.collected_expr_int;
            collected_expr_bv = other.collected_expr_bv;
            reg_vals = other.reg_vals;
        }

        void initialize(const PathState* path, uint32_t state) {
            path_state = path;
            automaton_state = state;
            collected_expr_int.clear();
            collected_expr_bv.clear();
            reg_vals.clear();
        }

        bool operator<(const MacroStateReal& other) const {
            if (automaton_state < other.automaton_state) {
                return true;
            } else if (other.automaton_state < automaton_state) {
                return false;
            } else {
                if (path_state->node_id < other.path_state->node_id) {
                    return true;
                } else if (other.path_state->node_id < path_state->node_id) {
                    return false;
                } else {
                    return reg_vals < other.reg_vals;
                }
            }
        }

        bool operator==(const MacroStateReal& other) const {
            return automaton_state == other.automaton_state &&
                   path_state->node_id == other.path_state->node_id &&
                   reg_vals == other.reg_vals;
        }

        bool check_constraints(z3::solver& solver) const {
            get_smt_ctx().solver_push(solver);
            for (const auto& atom : collected_expr_int) {
                get_smt_ctx().solver_add_condition(solver, atom);
            }

            auto result = get_smt_ctx().check(solver);
            if (result == z3::unknown) {
                get_smt_ctx().solver_pop(solver);
                z3::solver nra_solver = z3::tactic(*get_smt_ctx().get_context(), "qfnra").mk_solver();
                get_smt_ctx().solver_push(nra_solver);
                for (const auto& atom : collected_expr_int) {
                    nra_solver.add(atom);
                }
                if (nra_solver.check() == z3::sat) {
                    solver = nra_solver;
                    return true;
                }
                get_smt_ctx().solver_pop(nra_solver);
                return false;
            }

            switch (result) {
            case z3::sat:
                return true;
            case z3::unsat:
            case z3::unknown:
                get_smt_ctx().solver_pop(solver);
                return false;
            }

            return false;
        }
    };

    inline MacroStateReal init_macro_state_with_data(
            const PathState* path,
            uint32_t state,
            const std::vector<z3::expr>& expr_int,
            const std::vector<z3::expr>& expr_bv,
            const std::map<std::string, int64_t>& reg_vals)
    {
        return MacroStateReal {path, state, expr_int, expr_bv, reg_vals};
    }

    inline MacroStateReal copy_macro_state(const MacroStateReal& other) {
        return other;
    }

    inline MacroStateReal* init_macro_state(const PathState* path, uint32_t automaton) {
        auto* state = new MacroStateReal {};
        state->path_state = path;
        state->automaton_state = automaton;
        return state;
    }

} // namespace Paths::DataTest::RealModel

template<>
struct std::hash<Paths::DataTest::RealModel::MacroStateReal> {
    std::size_t operator() (const Paths::DataTest::RealModel::MacroStateReal & lhs) const {
        std::size_t seed = 0;
        auto hash_combine = [&seed](std::size_t value) {
            seed ^= value + 0x9e3779b97f4a7c15ULL + (seed << 6U) + (seed >> 2U);
        };

        hash_combine(std::hash<uint32_t>{}(lhs.automaton_state));
        hash_combine(std::hash<uint64_t>{}(lhs.path_state->node_id.id));

        for (const auto& expr : lhs.collected_expr_int) {
            hash_combine(static_cast<std::size_t>(expr.hash()));
        }
        for (const auto& expr : lhs.collected_expr_bv) {
            hash_combine(static_cast<std::size_t>(expr.hash()));
        }
        for (const auto& [name, value] : lhs.reg_vals) {
            hash_combine(std::hash<std::string>{}(name));
            hash_combine(std::hash<int64_t>{}(value));
        }

        return seed;
    }
};
