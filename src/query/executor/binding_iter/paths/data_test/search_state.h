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


        void print(std::ostream &os,
                   std::function<void(std::ostream &os, ObjectId)> print_node,
                   std::function<void(std::ostream &os, ObjectId, bool)> print_edge,
                   bool begin_at_left) const;



    };


    struct MacroState {
        const PathState *path_state;
        uint32_t automaton_state;
        std::map<std::string, double> upper_bounds;
        std::map<std::string, double> lower_bounds;
        std::map<std::string, double> eq_vals;
        z3::ast_vector_tpl<z3::expr> collected_expr = z3::ast_vector_tpl<z3::expr>(get_smt_ctx().context);


        MacroState(const PathState *path_state,
                   uint32_t automaton_state,
                   std::map<std::string, double> upper_bounds,
                   std::map<std::string, double> lower_bounds,
                   std::map<std::string, double> eq_vals,
                   const z3::ast_vector_tpl<z3::expr> &collected_expr

        ) :
                path_state(path_state),
                automaton_state(automaton_state),
                upper_bounds(std::move(upper_bounds)),
                lower_bounds(std::move(lower_bounds)),
                eq_vals(std::move(eq_vals)),
                collected_expr(collected_expr) {

        }

        MacroState(const PathState *path_state,
                   uint32_t automaton_state

        ) :
                path_state(path_state),
                automaton_state(automaton_state) {

        }

        MacroState(const MacroState &macro

        ) :
                path_state(macro.path_state),
                automaton_state(macro.automaton_state),
                upper_bounds(macro.upper_bounds),
                lower_bounds(macro.lower_bounds),
                eq_vals(macro.eq_vals),
                collected_expr(macro.collected_expr) {

        }

        int update_bound(std::tuple<Bound, z3::expr, z3::expr>);
        // For ordered set
        bool operator<(const MacroState& other) const {
            if (automaton_state < other.automaton_state) {
                return true;
            } else if (other.automaton_state < automaton_state) {
                return false;
            } else {
                return path_state -> node_id < other.path_state -> node_id;
            }
        }

        // For unordered set
        bool operator==(const MacroState& other) const {
            return automaton_state == other.automaton_state && path_state -> node_id == other.path_state -> node_id;
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