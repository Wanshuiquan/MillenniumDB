//
// Created by heyang-li on 6/25/25.
//

#include "naive_bfs_check.h"
#include "query/var_id.h"
#include "system/path_manager.h"
#include <optional>

using namespace std;
using namespace Paths::DataTest::Naive;

void NaiveBFSCheck::update_value(uint64_t obj) {
    for (const auto& key: attributes){
        ObjectId key_id = get<1>(key);
        auto res = query_property(obj, key_id.id);

        if (res.has_value()){
            uint64_t value_id = res.value();
            Result new_value = decode_mask(ObjectId(value_id));
            if (std::holds_alternative<std::string>(new_value)){
                string_attributes[key] = std::get<std::string>(new_value);
            }
            else if (std::holds_alternative<bool>(new_value)) {
                boolean_attributes[key] = std::get<bool>(new_value);
            }
            else {
                real_attributes[key] = std::get<std::double_t>(new_value);
            }
        }
    }
}

void NaiveBFSCheck::substitution(uint64_t obj, z3::ast_vector_tpl<z3::expr>& formulas, std::string formula)
{
    // update_value
    update_value(obj);
    exploration_depth++;
    // Initialize context
    for (const auto& ele: string_attributes){
        auto attr =  ele.first;
        std::string name = std::get<0>(attr);
        get_smt_ctx().add_string_var(name);
    }
    for (const auto& ele: real_attributes){
        auto attr =  ele.first;
        std::string name = std::get<0>(attr);
        get_smt_ctx().add_real_var(name);
    }
    for (const auto& ele: boolean_attributes){
        auto attr =  ele.first;
        std::string name = std::get<0>(attr);
        get_smt_ctx().add_bool_var(name);
    }
    for (const auto& ele: vars){
        auto var =  ele.first;
        get_smt_ctx().add_real_var(get_query_ctx().get_var_name(var));
    }
    //Parse Formula
    auto property = get_smt_ctx().parse(formula);
    //subsitution
    for (const auto& ele: string_attributes) {
        auto attr = ele.first;
        std::string name = std::get<0>(attr);
        std::string value = ele.second;
        property = get_smt_ctx().subsitute_string(name, value, property);
    }

    for (const auto& ele: real_attributes) {
        auto attr = ele.first;
        std::string name = std::get<0>(attr);
        double_t value = ele.second;
        property = get_smt_ctx().subsitute_real(name, value, property);
    }

    for (const auto& ele: boolean_attributes) {
        auto attr = ele.first;
        std::string name = std::get<0>(attr);
        bool value = ele.second;
        property = get_smt_ctx().subsitute_bool(name, value, property);
    }
    formulas.push_back(property);
}

void NaiveBFSCheck::_begin(Binding& _parent_binding) {

    parent_binding = &_parent_binding;
    first_next = true;
    iter = make_unique<NullIndexIterator>();

    // Init start object id
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();

    // Store ID for end object
    end_object_id = end.is_var() ? (*parent_binding)[end.get_var()] : end.get_OID();
    // init the start node
    auto* start_path_state =  visited.add(start_object_id,ObjectId::get_null(),ObjectId::get_null(), false,nullptr);

    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        z3::ast_vector_tpl<z3::expr>expr(get_smt_ctx().context);
        substitution(start_object_id.id, expr, t.property_checks);
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){


            open.emplace(start_path_state, t.to, expr);

        }
    }
}

const SearchState* NaiveBFSCheck::expand_neighbors(SearchState& search_state){
    // stop if automaton state has not outgoing transitions
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
            uint64_t edge_id = iter->get_edge();
            uint64_t target_id = iter->get_reached_node();
            // not allow cycle 
            if (!is_simple_path(search_state.path_state, ObjectId(iter->get_reached_node()))) {
                continue;
            }

            // progress with edges
            // edges type has checked, so we only check the properties
            // we do not progress if it is not sat with the edge transition, or the transition is not





            // else we explore a successor transition as a node transition
            for (auto &transition_node: automaton.from_to_connections[transition_edge.to]) {

                auto label_id = QuadObjectId::get_string(transition_node.type);
                bool matched_label = match_label(target_id, label_id.id);

                if (matched_label) {



                    auto new_state = visited.add(
                            search_state.path_state -> node_id,
                            search_state.path_state -> type_id,
                            search_state.path_state -> edge_id,
                            search_state.path_state -> inverse_dir,
                            search_state.path_state -> prev_state
                    );



                    substitution(edge_id, search_state.formulas, transition_edge.property_checks);
                    substitution(target_id, search_state.formulas, transition_edge.property_checks);
                    auto state= open.emplace(new_state, transition_node.to, search_state.formulas);
                    if (automaton.decide_accept(transition_node.to) && target_id == end_object_id.id) {
                        return &state;
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

bool NaiveBFSCheck::_next() {
    // Check if first state is final
    if (first_next) {
        auto& current_state = open.front();

        // iterate over each macro state



        auto node_iter = provider ->node_exists(current_state.path_state->  node_id.id);
        if (!node_iter){
            open.pop();
            return false;
        }
        // start state is the solution
        if (current_state.path_state-> node_id == end_object_id && automaton.decide_accept(current_state.automaton_state) && current_state.check_sat(s)) {
            auto path_id = path_manager.set_path(current_state.path_state, path_var);
            parent_binding->add(path_var, path_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(to_string(ele.second)));
            }
            queue<SearchState> empty;
            open.swap(empty);
            return true;

        }




    }

    // iterate
    while (!open.empty()) {
        // get a new state vector
        auto &current_state = open.front();
        auto reached_final_state = expand_neighbors(current_state);

        // Enumerate reached solutions
        if (reached_final_state != nullptr && current_state.check_sat(s)) {
            auto path_id = path_manager.set_path(reached_final_state->path_state, path_var);
            parent_binding->add(path_var, path_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(to_string(ele.second)));
            }
            return true;
        } else {
            // Pop and visit next state
            open.pop();
        }
    }
    return false;
}


void NaiveBFSCheck::_reset() {
    // Empty open and visited
    queue<SearchState> empty;
    open.swap(empty);
    visited.clear();
    first_next = true;
    iter = make_unique<NullIndexIterator>();

    // Add starting states to open and visited
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();

    auto* start_search_state =  visited.add(start_object_id,
        ObjectId::get_null(),
        ObjectId::get_null(),
        false,
        nullptr);

    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        z3::ast_vector_tpl<z3::expr> vec(get_smt_ctx().context);
        substitution(start_object_id.id, vec, t.property_checks);
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){
            // the next transition should be an edge transition

            open.emplace(start_search_state, t.to, vec);


        }
    }
    // insert the init state vector to the state
    // Store ID for end object
    end_object_id = end.is_var() ? (*parent_binding)[end.get_var()] : end.get_OID();
}


void NaiveBFSCheck::accept_visitor(BindingIterVisitor& visitor) {
    visitor.visit(*this);
}
