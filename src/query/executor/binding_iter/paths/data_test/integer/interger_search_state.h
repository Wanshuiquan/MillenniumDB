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
namespace Paths::DataTest {



   // Macro State to store the formulas
    struct MacroStateInt {
        const PathState* path_state;
        uint32_t automaton_state;
        std::map<int64_t, double> upper_bounds;
        std::map<int64_t, double> lower_bounds;
        std::map<int64_t, double> eq_vals;
        std::vector<int64_t> collected_expr_int;
        std::vector<int64_t> collected_expr_bv;

        int update_bound(std::tuple<Bound, int64_t, z3::expr>);
        void initialize_from(const MacroStateInt& other);
        void initialize(const PathState* path, uint32_t state);
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

} // namespace Paths::DataTest

template<>
struct std::hash<Paths::DataTest::MacroStateInt> {
    std::size_t operator() (const Paths::DataTest::MacroStateInt & lhs) const {
        return lhs.automaton_state ^ lhs.path_state->node_id.id;
    }
};

