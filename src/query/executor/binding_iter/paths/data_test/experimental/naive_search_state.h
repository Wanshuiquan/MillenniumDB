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
struct NaivePathState {

    ObjectId node_id;
    ObjectId type_id;
    ObjectId edge_id;
    bool inverse_dir;
    uint64_t automaton_state;
    z3::ast_vector_tpl<z3::expr> formulas = z3::ast_vector_tpl<z3::expr>(get_smt_ctx().context);
    const NaivePathState *prev_state;

    NaivePathState() = default;

    NaivePathState(ObjectId object_id,
              ObjectId type_id,
              ObjectId edge_id,
              bool inverse_dir,
              const NaivePathState *prev_state) :
        node_id(object_id),
        type_id(type_id),
        edge_id(edge_id),
        inverse_dir(inverse_dir), automaton_state(0),
        prev_state(prev_state) {}

    NaivePathState(ObjectId object_id,
                   ObjectId type_id,
                   ObjectId edge_id,
                   bool inverse_dir,
                   const NaivePathState *prev_state,
                   uint64_t automaton_state) :
        node_id(object_id),
        type_id(type_id),
        edge_id(edge_id),
        inverse_dir(inverse_dir),
        prev_state(prev_state),
        automaton_state(automaton_state){}


    NaivePathState(ObjectId object_id,
          ObjectId type_id,
          ObjectId edge_id,
          bool inverse_dir,
          const NaivePathState *prev_state,
          uint64_t automaton_state,
          z3::ast_vector_tpl<z3::expr> f) :
        node_id(object_id),
        type_id(type_id),
        edge_id(edge_id),
        inverse_dir(inverse_dir),
        prev_state(prev_state),
        automaton_state(automaton_state)
    {
        for (const auto & formula : f) {
            formulas.push_back(formula);
        }
    }

    void print(std::ostream &os,
               std::function<void(std::ostream &os, ObjectId)> print_node,
               std::function<void(std::ostream &os, ObjectId, bool)> print_edge,
               bool begin_at_left) const;

    bool check_sat(z3::solver&s)
    {
        for (const auto& f: formulas) {
            s.add(f);
        }
        switch (s.check()) {
            case z3::unsat: return false;
            case z3::sat: return true;
            case z3::unknown: return false;
            default: return false;
        }
    }


};

}

inline bool is_simple_path(const Paths::DataTest::Naive::NaivePathState* path_state, ObjectId new_node) {
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
struct std::hash<Paths::DataTest::Naive::NaivePathState> {
    std::size_t operator() (const Paths::DataTest::Naive::NaivePathState & lhs) const {
        return lhs.automaton_state ^ lhs.node_id.id;
    }
};
#endif //NAIVE_SEARCH_STATE_H
