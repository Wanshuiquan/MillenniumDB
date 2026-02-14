#include "search_state.h"
using namespace Paths::DataTest;


void PathState::print(std::ostream& os,
                      std::function<void(std::ostream& os, ObjectId)> print_node,
                      std::function<void(std::ostream& os, ObjectId, bool)> print_edge,
                      bool begin_at_left) const
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


int MacroState::update_bound(std::tuple<Bound, int64_t, z3::expr> bound) {
    auto type = std::get<0>(bound);
    auto key = std::get<1>(bound);
    auto value = std::get<2>(bound);
    collected_expr->push_back(key);

    switch (type) {
        case Le: {
            if (upper_bounds->find(key) == upper_bounds->end()) {
                (*upper_bounds)[key] = value.as_double();  // Dereference pointer first
            }
            else {
                double old_bound = (*upper_bounds)[key];  // Dereference pointer first
                double new_bound = value.as_double();
                if (new_bound < old_bound) (*upper_bounds)[key] = new_bound;
            }
            return 1;
        }
        case Ge: {
            if (lower_bounds->find(key) == lower_bounds->end()) {
                (*lower_bounds)[key] = value.as_double();  // Dereference pointer first
            }
            else {
                double old_bound = (*lower_bounds)[key];  // Dereference pointer first
                double new_bound = value.as_double();
                if (new_bound > old_bound) (*lower_bounds)[key] = new_bound;
            }
            return 1;
        }
        case EQ: {
            if (eq_vals->find(key) == eq_vals->end()) {
                (*eq_vals)[key] = value.as_double();  // Dereference pointer first
                return 1;
            }
            else {
                double old_bound = (*eq_vals)[key];  // Dereference pointer first
                double new_bound = value.as_double();
                return int(new_bound == old_bound);
            }
        }
        default: return 0;
    }
}

void MacroState::initialize_from(const Paths::DataTest::MacroState &other) {
    path_state = other.path_state;
    automaton_state = other.automaton_state;
    upper_bounds = new std::map<int64_t, double>(*other.upper_bounds);
    lower_bounds = new std::map<int64_t, double>(*other.lower_bounds);
    eq_vals = new std::map<int64_t, double>(*other.eq_vals);
    collected_expr = new std::vector<int64_t>(*other.collected_expr);
}

void MacroState::initialize(const Paths::DataTest::PathState *path, uint32_t state) {
    path_state = path;
    automaton_state = state;
    upper_bounds = new std::map<int64_t, double>();
    lower_bounds = new std::map<int64_t, double>();
    eq_vals = new std::map<int64_t, double>();
    collected_expr = new std::vector<int64_t>();
}
