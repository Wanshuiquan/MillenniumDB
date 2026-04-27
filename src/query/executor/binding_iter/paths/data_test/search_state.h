#pragma once

#include <functional>
#include <vector>
#include "graph_models/object_id.h"
#include "query/executor/binding_iter/paths/index_provider/path_index.h"
#include "query/smt/smt_ctx.h"
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
                const std::function<void(ObjectId)>& node_func,
                const std::function<void(ObjectId, bool)>& edge_func,
                bool begin_at_left
        ) const;



    };
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
         bool operator==(const PreSearchState& other) const {
             return automaton_state == other.automaton_state &&
                    path_state->node_id == other.path_state->node_id;
         }

        bool operator<(const PreSearchState& other) const {
            if (automaton_state < other.automaton_state) {
                return true;
            } else if (other.automaton_state < automaton_state) {
                return false;
            } else {
                return path_state->node_id < other.path_state->node_id;
            }
        }
     };
}



template<>
struct std::hash<Paths::DataTest::PreSearchState> {
    std::size_t operator() (const Paths::DataTest::PreSearchState & lhs) const {
        return lhs.automaton_state ^ lhs.path_state->node_id.id;
    }
};