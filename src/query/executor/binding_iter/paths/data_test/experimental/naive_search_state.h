//
// Created by heyang-li on 6/25/25.
//

#ifndef NAIVE_SEARCH_STATE_H
#define NAIVE_SEARCH_STATE_H

#pragma once

#include <functional>
#include <ostream>
#include "graph_models/object_id.h"
#include "query/executor/binding_iter/paths/index_provider/path_index.h"
#include "query/smt/smt_ctx.h"

namespace Paths::DataTest::Naive {
struct PathState {
    ObjectId node_id;
    ObjectId type_id;
    ObjectId edge_id;
    bool inverse_dir;
    const PathState *prev_state;

    PathState()=default;
    PathState(ObjectId node_id,
    ObjectId type_id,
    ObjectId edge_id,
    bool inverse_dir,
    const PathState* prev):
        node_id(node_id),
        type_id(type_id),
        edge_id(edge_id),
        inverse_dir(inverse_dir),
        prev_state(prev)
        {}


    void for_each(
            std::function<void(ObjectId)> node_func,
            std::function<void(ObjectId, bool)> edge_func,
            bool begin_at_left
    ) const;

};

struct SearchState{
    const PathState* path_state;
    uint32_t  automaton_state;
    z3::ast_vector_tpl<z3::expr> formulas;

    SearchState(const PathState* path_state, uint32_t automaton_state):
        path_state(path_state),
        automaton_state(automaton_state),
        formulas(z3::ast_vector_tpl<z3::expr>(*get_smt_ctx().get_context())){

    }

    SearchState(const SearchState& other)
            : path_state(other.path_state),
              automaton_state(other.automaton_state),
              formulas(other.formulas.ctx()) { // Initialize with the same context
        for (const auto& expr : other.formulas) {
            formulas.push_back(expr);
        }
    }

    SearchState(const PathState* path_state,
                uint32_t automaton_state,
                z3::ast_vector_tpl<z3::expr>& f):
            path_state(path_state),
            automaton_state(automaton_state),
            formulas(z3::ast_vector_tpl<z3::expr>(*get_smt_ctx().get_context()))
            {
            for(const auto& p: f){
                formulas.push_back(p);
            }
    }





    bool operator<(const SearchState& other) const {
        if (automaton_state < other.automaton_state) {
            return true;
        } else if (other.automaton_state < automaton_state) {
            return false;
        } else {
            return path_state -> node_id < other.path_state -> node_id;
        }
    }

    // For unordered set
    bool operator==(const SearchState& other) const {
        return automaton_state == other.automaton_state && path_state -> node_id == other.path_state -> node_id;
    }

};

}

inline bool is_simple_path(const Paths::DataTest::Naive::PathState* path_state, ObjectId new_node) {
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
struct std::hash<Paths::DataTest::Naive::SearchState> {
    std::size_t operator() (const Paths::DataTest::Naive::SearchState & lhs) const {
        return lhs.automaton_state ^ lhs.path_state -> node_id.id;
    }
};
#endif //NAIVE_SEARCH_STATE_H
