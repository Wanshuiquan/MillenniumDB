#pragma once

#include <functional>
#include <ostream>
#include <cstdint>
#include <tuple>

#include <utility>
#include <vector>
#include <map>
#include "graph_models/object_id.h"
#include "query/smt/smt_expr/smt_exprs.h"
#include "query/smt/smt_ctx.h"
#include "query/executor/binding_iter/paths/data_test/search_state.h"
namespace Paths::DataTest::LRA {



   // Macro State to store the formulas
    struct MacroState {
        const PathState* path_state;
        uint32_t automaton_state;
        std::map<int64_t, double> upper_bounds;
        std::map<int64_t, double> lower_bounds;
        std::map<int64_t, double> eq_vals;
        std::vector<int64_t> collected_expr;

        int update_bound(std::tuple<Bound, int64_t, z3::expr>);
        void initialize_from(const MacroState& other);
        void initialize(const PathState* path, uint32_t state);
        bool operator<(const MacroState& other) const {
            if (automaton_state < other.automaton_state) {
                return true;
            } else if (other.automaton_state < automaton_state) {
                return false;
            } else {
                return path_state->node_id < other.path_state->node_id;
            }
        }

        bool operator==(const MacroState& other) const {
            return automaton_state == other.automaton_state &&
                   path_state->node_id == other.path_state->node_id;
        }
    };


// Factory functions outside the struct
    inline MacroState init_macro_state_with_data(const PathState* path,
                        uint32_t state,
                        const std::map<int64_t, double>& ub,
                        const std::map<int64_t, double>& lb,
                        const std::map<int64_t, double>& eq,
                        const std::vector<int64_t>& expr) {
        return MacroState{path, state, ub, lb, eq, expr};
    }
    inline MacroState copy_macro_state(const MacroState& other) {
        return other;
    }
    inline MacroState* init_macro_state(const PathState* path, uint32_t automaton) {
        auto* state = new MacroState{};
        state->path_state = path;
        state->automaton_state = automaton;
        return state;
    }


}


template<>
struct std::hash<Paths::DataTest::LRA::MacroState> {
    std::size_t operator() (const Paths::DataTest::LRA::MacroState & lhs) const {
        return lhs.automaton_state ^ lhs.path_state->node_id.id;
    }
};

