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
#include "z3++.h"

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


    void print(std::ostream &os,
               std::function<void(std::ostream & os, ObjectId)> print_node,
               std::function<void(std::ostream & os, ObjectId, bool)> print_edge,
               bool begin_at_left) const {
        if (begin_at_left) {
            // the path need to be reconstructed in the reverse direction (last seen goes first)
            std::vector<ObjectId> nodes;
            std::vector<ObjectId> edges;
            std::vector<bool> inverse_directions;

            for (auto current_state = this; current_state != nullptr; current_state = current_state->prev_state) {
                nodes.push_back(current_state->node_id);
                edges.push_back(current_state->type_id);
                inverse_directions.push_back(current_state->inverse_dir);
            }

            print_node(os, nodes[nodes.size() - 1]);
            for (int_fast32_t i = nodes.size() - 2; i >= 0; i--) { // don't use unsigned i, will overflow
                print_edge(os, edges[i], inverse_directions[i]);
                print_node(os, nodes[i]);
            }
        } else {
            auto current_state = this;
            print_node(os, current_state->node_id);

            while (current_state->prev_state != nullptr) {
                print_edge(os, current_state->type_id, !current_state->inverse_dir);
                current_state = current_state->prev_state;
                print_node(os, current_state->node_id);
            }
        }
    }

};

struct SearchState{
    const PathState* path_state;
    uint32_t  automaton_state;
    z3::ast_vector_tpl<z3::expr> formulas;

    SearchState(const PathState* path_state, uint32_t automaton_state):
        path_state(path_state),
        automaton_state(automaton_state),
        formulas(z3::ast_vector_tpl<z3::expr>(get_smt_ctx().context)){

    }

    SearchState(const PathState* path_state,
                uint32_t automaton_state,
                z3::ast_vector_tpl<z3::expr>& f):
            path_state(path_state),
            automaton_state(automaton_state),
            formulas(z3::ast_vector_tpl<z3::expr>(get_smt_ctx().context))
            {
            for(const auto& p: f){
                formulas.push_back(p);
            }
    }



    bool check_sat(z3::solver&s)
    {
        for (const auto& f: formulas) {
            s.add(f);
        }
        s.push();
        auto s1 = s.to_smt2();
        switch (s.check()) {
            case z3::unsat:s.pop(); return false;
            case z3::sat: s.pop(); return true;
            case z3::unknown: s.pop(); return false;
            default: return false;
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
