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
namespace Paths::DataTest {



   // Macro State to store the formulas
    struct MacroStateInt {
        const PathState* path_state;
        uint32_t automaton_state;
        std::vector<z3::expr> collected_expr_int;
        std::vector<z3::expr> collected_expr_bv;

        void initialize_from(const MacroStateInt& other) {
            path_state = other.path_state;
            automaton_state = other.automaton_state;
            collected_expr_int = other.collected_expr_int;
            collected_expr_bv = other.collected_expr_bv;
        }

        void initialize(const Paths::DataTest::PathState* path, uint32_t state) {
            path_state = path;
            automaton_state = state;
            collected_expr_int.clear();
            collected_expr_bv.clear();
        }

        bool operator<(const MacroStateInt& other) const {
            if (automaton_state < other.automaton_state) {
                return true;
            } else if (other.automaton_state < automaton_state) {
                return false;
            } else {
                return path_state->node_id < other.path_state->node_id;
            }
        }

        bool operator==(const MacroStateInt& other) const {
            return automaton_state == other.automaton_state &&
                   path_state->node_id == other.path_state->node_id;
        }
    };

    inline MacroStateInt init_macro_state_with_data(
            const PathState* path,
            uint32_t state,
            const std::vector<z3::expr>& expr_int,
            const std::vector<z3::expr>& expr_bv)
    {
        return MacroStateInt {path, state, expr_int, expr_bv};
    }

    inline MacroStateInt copy_macro_state(const MacroStateInt& other) {
        return other;
    }

    inline MacroStateInt* init_macro_state(const PathState* path, uint32_t automaton) {
        auto* state = new MacroStateInt {};
        state->path_state = path;
        state->automaton_state = automaton;
        return state;
    }

} // namespace Paths::DataTest

template<>
struct std::hash<Paths::DataTest::MacroStateInt> {
    std::size_t operator() (const Paths::DataTest::MacroStateInt & lhs) const {
        return lhs.automaton_state ^ lhs.path_state->node_id.id;
    }
};

