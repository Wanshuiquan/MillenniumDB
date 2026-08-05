//
// Created by heyang-li on 3/16/26.
//
#include <cassert> 
#include "preprocess_dfs_enum.h"
#include "query_data.h"
using namespace std; 
using namespace Paths::DataTest; 

void DFSPreEnum::_begin(Binding& _parent_binding)
{
    parent_binding = &_parent_binding;
    iter = make_unique<NullIndexIterator>();
    first_next = true;

    // Init start object id
    current_start = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();

    // Store ID for end object
    // init the start node
    auto* start_path_state = visited.add(current_start, ObjectId(), ObjectId() , false, nullptr);
    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(current_start.id, label_id);

        if (label_matched){
            auto it = visited_product_graph.emplace(start_path_state, t.to);
            if (it.second) {
                open.push(it.first.operator*());
            }
        }
        // insert the init state vector to the state
    }
}

const PathState* DFSPreEnum::expand_neighbors(PreSearchState& search_state) {
    // stop if automaton state has not outgoing transitions
    // Check if this is the first time that current_state is explored
    if (iter->at_end()) {
        current_transition = 0;
        // Check if automaton state has transitions
        if (automaton.from_to_connections[search_state.automaton_state].empty()) {
            return nullptr;
        }
        set_iter(search_state);
    }

    while (current_transition < automaton.from_to_connections[search_state.automaton_state].size()) {
        auto &transition_edge = automaton.from_to_connections[search_state.automaton_state][current_transition];
        while (iter->next()) {
            // get the edge of edge and target
            uint64_t target_id = iter->get_reached_node();

            uint64_t edge_id = iter->get_edge();
            // else we explore a successor transition as a node transition
            for (auto &transition_node: automaton.from_to_connections[transition_edge.to]) {
                auto label_id = QuadObjectId::get_string(transition_node.type);
                bool matched_label = match_label(target_id, label_id.id);

                if (matched_label) {
                    auto* new_ptr  = visited.add(
                            ObjectId(target_id),
                            transition_edge.type_id,
                            ObjectId(edge_id),
                            transition_edge.inverse,
                             search_state.path_state
                    );

                    auto new_state = visited_product_graph.emplace(new_ptr, transition_node.to);
                    if (new_state.second) {
                        open.push(new_state.first.operator*());
                    }
                    if (automaton.decide_accept(transition_node.to)) {
                        return new_ptr;
                    }
                }
            }


        }
        current_transition++;
        if (current_transition < automaton.from_to_connections[search_state.automaton_state].size()) {
            set_iter(search_state);
        }

    }
    return nullptr;

}
bool DFSPreEnum::_next() {
    if (!first_next) {
        return false;
    }
    first_next = false;

    while (!open.empty()) {
        auto current_state = open.top();
        open.pop();

        if (!provider->node_exists(current_state.path_state->node_id.id)) {
            continue;
        }

        if (automaton.decide_accept(current_state.automaton_state)) {
            return true;
        }

        if (automaton.from_to_connections[current_state.automaton_state].empty()) {
            continue;
        }

        current_transition = 0;
        set_iter(current_state);

        while (current_transition < automaton.from_to_connections[current_state.automaton_state].size()) {
            auto& transition_edge = automaton.from_to_connections[current_state.automaton_state][current_transition];
            while (iter->next()) {
                uint64_t target_id = iter->get_reached_node();
                uint64_t edge_id = iter->get_edge();

                for (auto& transition_node : automaton.from_to_connections[transition_edge.to]) {
                    auto label_id = QuadObjectId::get_string(transition_node.type);
                    bool matched_label = match_label(target_id, label_id.id);

                    if (!matched_label) {
                        continue;
                    }

                    auto* new_ptr = visited.add(
                        ObjectId(target_id),
                        transition_edge.type_id,
                        ObjectId(edge_id),
                        transition_edge.inverse,
                        current_state.path_state
                    );

                    auto new_state = visited_product_graph.emplace(new_ptr, transition_node.to);
                    if (!new_state.second) {
                        continue;
                    }

                    if (automaton.decide_accept(transition_node.to)) {
                        return true;
                    }

                    open.push(*new_state.first);
                }
            }

            current_transition++;
            if (current_transition < automaton.from_to_connections[current_state.automaton_state].size()) {
                set_iter(current_state);
            }
        }
    }
    return false;
}





void DFSPreEnum::_reset() {
    // Empty open and visited
    stack<PreSearchState> empty;
    open.swap(empty);
    visited.clear();
    visited_product_graph.clear();
    first_next = true;
    iter = make_unique<NullIndexIterator>();
    // Add starting states to open and visited
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    PathState *start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null() , false, nullptr);


    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){
            auto it = visited_product_graph.emplace(start_path_state,t.to);
            // the next transition should be an edge transition
            if (it.second) {
                open.push(it.first.operator*());
            }
        }
    }
    // insert the init state vector to the state
}

void DFSPreEnum::print(std::ostream& os, int indent, bool stats) const
{
    if (stats) {
        if (stats) {
            os << std::string(indent, ' ') << "\n[begin: " << stat_begin << " next: " << stat_next
               << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches
               << "]\n";
        }
    }
    os << std::string(indent, ' ') << "Paths::DATA::DFSPreEnum(path_var: " << ", start: " << start << ", end: " << ")";
}
