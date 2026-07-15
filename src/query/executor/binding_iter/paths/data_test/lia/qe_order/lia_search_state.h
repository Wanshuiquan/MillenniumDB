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
namespace Paths::DataTest::LIA {



   // Macro State to store the formulas
    struct MacroState {
        const PathState* path_state;
        uint32_t automaton_state;
        std::map<int64_t, int64_t> upper_bounds;
        std::map<int64_t, int64_t> lower_bounds;
        std::map<int64_t, int64_t> eq_vals;
        std::map<int64_t, int64_t> gt_vals;
        std::map<int64_t, int64_t> lt_vals;
        std::map<int64_t, std::vector<int64_t>> neq_vals;
        std::vector<int64_t> collected_expr;
        std::map<std::string, int64_t> reg_vals;

        int update_bound(std::tuple<Bound, int64_t, z3::expr>);
        void initialize_from(const MacroState& other);
        void initialize(const PathState* path, uint32_t state);
        bool operator<(const MacroState& other) const {
            if (automaton_state < other.automaton_state) {
                return true;
            } else if (other.automaton_state < automaton_state) {
                return false;
            } else if (path_state->node_id < other.path_state->node_id) {
                return true;
            } else if (other.path_state->node_id < path_state->node_id) {
                return false;
            } else {
                return reg_vals < other.reg_vals;
            }
        }

        bool operator==(const MacroState& other) const {
            return automaton_state == other.automaton_state &&
                   path_state->node_id == other.path_state->node_id &&
                   reg_vals == other.reg_vals;
        }
    };


// Factory functions outside the struct
    inline MacroState init_macro_state_with_data(const PathState* path,
                        uint32_t state,
                        const std::map<int64_t, int64_t>& ub,
                        const std::map<int64_t, int64_t>& lb,
                        const std::map<int64_t, int64_t>& eq,
                        const std::map<int64_t, int64_t>& gt,
                        const std::map<int64_t, int64_t>& lt,
                        const std::map<int64_t, std::vector<int64_t>>& neq,
                        const std::vector<int64_t>& expr,
                        const std::map<std::string, int64_t>& reg) {
        return MacroState{path, state, ub, lb, eq, gt, lt, neq, expr, reg};
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
struct std::hash<Paths::DataTest::LIA::MacroState> {
    std::size_t operator() (const Paths::DataTest::LIA::MacroState & lhs) const {
        std::size_t seed = 0;
        auto hash_combine = [&seed](std::size_t value) {
            seed ^= value + 0x9e3779b97f4a7c15ULL + (seed << 6U) + (seed >> 2U);
        };

        hash_combine(std::hash<uint32_t>{}(lhs.automaton_state));
        hash_combine(std::hash<uint64_t>{}(lhs.path_state->node_id.id));

        for (const auto& [expr_id, value] : lhs.upper_bounds) {
            hash_combine(std::hash<int64_t>{}(expr_id));
        }
        for (const auto& [expr_id, value] : lhs.lower_bounds) {
            hash_combine(std::hash<int64_t>{}(expr_id));
        }

        for (const auto& [expr_id, value] : lhs.gt_vals) {
            hash_combine(std::hash<int64_t>{}(expr_id));
        }
        for (const auto& [expr_id, value] : lhs.lt_vals) {
            hash_combine(std::hash<int64_t>{}(expr_id));
        }
        for (const auto& [expr_id, value] : lhs.eq_vals) {
            hash_combine(std::hash<int64_t>{}(expr_id));
        }
        for (const auto& [expr_id, values] : lhs.neq_vals) {
            hash_combine(std::hash<int64_t>{}(expr_id));
            for (const auto& value : values) {
            }
        }
        for (const auto& expr_id : lhs.collected_expr) {
            hash_combine(std::hash<int64_t>{}(expr_id));
        }

        for (const auto& [reg_name, reg_val] : lhs.reg_vals) {
            hash_combine(std::hash<std::string>{}(reg_name));
            hash_combine(std::hash<int64_t>{}(reg_val));
        }

        return seed;
    }
};

