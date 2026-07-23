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

namespace Paths::DataTest::LIA_SubsetOrder {
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
    std::map<std::string, int64_t> reg_vals;

    SearchState(const PathState* path_state, uint32_t automaton_state):
        path_state(path_state),
        automaton_state(automaton_state),
        formulas(z3::ast_vector_tpl<z3::expr>(*get_smt_ctx().get_context())){

    }

    SearchState(const SearchState& other)
            : path_state(other.path_state),
              automaton_state(other.automaton_state),
              formulas(other.formulas.ctx()),
              reg_vals(other.reg_vals) { // Initialize with the same context
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
template<>
struct std::hash<Paths::DataTest::LIA_SubsetOrder::SearchState> {
    std::size_t operator() (const Paths::DataTest::LIA_SubsetOrder::SearchState & lhs) const {
        std::size_t seed = 0;
        auto hash_combine = [&seed](std::size_t value) {
            seed ^= value + 0x9e3779b97f4a7c15ULL + (seed << 6U) + (seed >> 2U);
        };

        hash_combine(std::hash<uint32_t>{}(lhs.automaton_state));
        hash_combine(std::hash<uint64_t>{}(lhs.path_state->node_id.id));
        for (const auto& formula : lhs.formulas) {
            hash_combine(static_cast<std::size_t>(formula.hash()));
        }
        return seed;
    }
};
#endif //NAIVE_SEARCH_STATE_H
