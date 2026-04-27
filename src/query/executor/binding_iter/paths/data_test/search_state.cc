#include "search_state.h"
using namespace Paths::DataTest;


void PathState::for_each(
const std::function<void(ObjectId)>& node_func,
const std::function<void(ObjectId, bool)>& edge_func,
bool begin_at_left
) const
{
    if (begin_at_left) {
        // the path need to be reconstructed in the reverse direction (last seen goes first)
        std::vector<ObjectId> nodes;
        std::vector<ObjectId> edges;
        std::vector<bool>     inverse_directions;

        for (auto current_state = this; current_state != nullptr; current_state = current_state->prev_state) {
            nodes.push_back(current_state->node_id);
            edges.push_back(current_state->type_id);
            inverse_directions.push_back(current_state->inverse_dir);
        }

        if (nodes.empty()) {
            return;
        }

        node_func(nodes.back());
        for (size_t rev = nodes.size() - 1; rev > 0; --rev) {
            const size_t i = rev - 1;
            edge_func(edges[i], inverse_directions[i]);
            node_func(nodes[i]);
        }
    } else {
        auto current_state = this;
        node_func(current_state->node_id);

        while (current_state->prev_state != nullptr) {
            edge_func(current_state->type_id, !current_state->inverse_dir);
            current_state = current_state->prev_state;
            node_func(current_state->node_id);
        }
    }
}