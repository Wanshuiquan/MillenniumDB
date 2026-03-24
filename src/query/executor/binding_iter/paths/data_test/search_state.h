#pragma once

#include <functional>
#include <ostream>

#include <utility>
#include <vector>
#include <map>
#include "graph_models/object_id.h"
#include "query/executor/binding_iter/paths/index_provider/path_index.h"
#include "query/smt/smt_expr/smt_exprs.h"
#include "query/smt/smt_ctx.h"
#include "z3++.h"
namespace Paths::DataTest {

    // Represents a path in a recursive manner (prev_state points to previous path state)
    struct PathState {
        ObjectId node_id;
        ObjectId type_id;
        ObjectId edge_id;
        bool inverse_dir;
        const PathState *prev_state;

        PathState() = default;

        PathState(ObjectId object_id,
                  ObjectId type_id,
                  ObjectId edge_id,
                  bool inverse_dir,
                  const PathState *prev_state) :
                node_id(object_id),
                type_id(type_id),
                edge_id(edge_id),
                inverse_dir(inverse_dir),
                prev_state(prev_state) {}


        void for_each(
                std::function<void(ObjectId)> node_func,
                std::function<void(ObjectId, bool)> edge_func,
                bool begin_at_left
        ) const;



    };

   // Macro State to store the formulas
    struct MacroState {
        const PathState* path_state;
        uint32_t automaton_state;
        std::map<int64_t, double>* upper_bounds;
        std::map<int64_t, double>* lower_bounds;
        std::map<int64_t, double>* eq_vals;
        std::vector<int64_t>* collected_expr;

        // Remove all constructors - let it be trivially constructible
        // MacroState() = default; // Don't even need this

        int update_bound(std::tuple<Bound, int64_t, z3::expr>);
        void initialize_from(const MacroState& other);
        void initialize(const PathState* path, uint32_t state);
        // Helper to clean up (call before Arena reclaims memory)
        void cleanup() const {
            delete upper_bounds;
            delete lower_bounds;
            delete eq_vals;
            delete collected_expr;
        }
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
                        std::map<int64_t, double>* ub,
                        std::map<int64_t, double>* lb,
                        std::map<int64_t, double>* eq,
                        std::vector<int64_t>* expr) {
        return MacroState{
                path,
                state,
                new std::map<int64_t, double>(*ub),
                new std::map<int64_t, double>(*lb),
                new std::map<int64_t, double>(*eq),
                new std::vector<int64_t>(*expr)
        };
    }
    inline MacroState copy_macro_state(const MacroState& other) {
        return MacroState{
                other.path_state,
                other.automaton_state,
                new std::map<int64_t, double>(*other.upper_bounds),
                new std::map<int64_t, double>(*other.lower_bounds),
                new std::map<int64_t, double>(*other.eq_vals),
                new std::vector<int64_t>(*other.collected_expr)
        };
    }
    inline MacroState* init_macro_state(const PathState* path, uint32_t automaton) {
        auto* state = new MacroState{};
        state->path_state = path;
        state-> automaton_state = automaton;
        state->upper_bounds = new std::map<int64_t, double>();
        state->lower_bounds = new std::map<int64_t, double>();
        state->eq_vals = new std::map<int64_t, double>();
        state->collected_expr = new std::vector<int64_t>();
        return state;
    }

    struct PreSearchState
     {
         const PathState* path_state;
         uint32_t automaton_state;
        PreSearchState() = default;

        PreSearchState(
             const PathState* path,
             uint32_t automaton_state
             ):
             path_state(path), automaton_state(automaton_state)
         {}
         bool operator==(const MacroState& other) const {
             return automaton_state == other.automaton_state &&
                    path_state->node_id == other.path_state->node_id;
         }
     };
}
inline bool is_simple_path(const Paths::DataTest::PathState* path_state, ObjectId new_node) {
    // Iterate over path backwards
    auto current = path_state;
    while (current != nullptr) {
        // Path is not simple (two nodes are equal)
        if (current->node_id == new_node) {
            return false;
        }
        current = current->prev_state;
    }
    return true;
}

template<>
struct std::hash<Paths::DataTest::MacroState> {
    std::size_t operator() (const Paths::DataTest::MacroState & lhs) const {
        return lhs.automaton_state ^ lhs.path_state->node_id.id;
    }
};