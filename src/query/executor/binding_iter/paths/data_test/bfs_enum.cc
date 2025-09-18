//
// Created by lhy on 9/2/24.
//
#include <cassert>

#include "bfs_enum.h"

#include "query/var_id.h"
#include "system/path_manager.h"
#include "z3++.h"
using namespace std;
using namespace Paths::DataTest;

// we can deduce the type from here
void BFSEnum::update_value(uint64_t obj) {
    for (const auto& ele: attributes){
        auto key = ele;
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

bool BFSEnum::eval_check(uint64_t obj, MacroState& macroState, std::string formula) {
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
    //substitution
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
    // decompose
    auto vector = get_smt_ctx().decompose(property);

    for (const auto& f: vector) {
        // normalize formula into t ~ constant
        auto normal_form = get_smt_ctx().normalizition(f);
        // if the formula is normalized as constant
        if (normal_form.is_true()) {
            continue;
        } else if (normal_form.is_false()) {
            return false;
        }
        // get and update the bound
        auto bound = get_smt_ctx().get_bound(normal_form);
        auto update_flag = macroState.update_bound(bound);
        // update the wrong value
        if (update_flag == 0) {
            return false;
        }
    }
    //check the sat for the current bound
//        solver.reset();
    solver.push();
    solver.add(get_smt_ctx().bound_epsilon);
    std::set<int64_t> visited_parameter;

    for (const auto &para: macroState.collected_expr) {
        const int64_t &key_str = para.hash();
        if (visited_parameter.find(key_str) != visited_parameter.end()) {
            continue;
        }else {
            visited_parameter.emplace(key_str);
        }
        auto parameter = para;

        if (macroState.upper_bounds.find(key_str) != macroState.upper_bounds.end()) {
            double val = macroState.upper_bounds[key_str];
            solver.add(parameter <= get_smt_ctx().add_real_val(val));
        }

        if (macroState.lower_bounds.find(key_str) != macroState.lower_bounds.end()) {
            double val = macroState.lower_bounds[key_str];
            solver.add(parameter >= get_smt_ctx().add_real_val(val));
        }

        if (macroState.eq_vals.find(key_str) != macroState.eq_vals.end()) {
            double val = macroState.eq_vals[key_str];
            solver.add(parameter == get_smt_ctx().add_real_val(val));
        }
    }

    switch (solver.check()) {
        case z3::sat: {
            auto model = solver.get_model();
            for (const auto &ele:vars){
                std::string name = get_query_ctx().get_var_name(ele.first);
                z3::expr v = get_smt_ctx().get_var(name);
                auto val = model.eval(v).as_double();
                vars[ele.first] = val;
            }
            solver.pop();
            assert(solver.assertions().empty());
            return true;
        }
        case z3::unsat: {
            solver.pop();

            return false;
        }
        case z3::unknown: return false;
    }
}


void BFSEnum::_begin(Binding& _parent_binding) {
    parent_binding = &_parent_binding;
    first_next = true;
    iter = make_unique<NullIndexIterator>();

    // Init start object id
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();

    // Store ID for end object
    // init the start node
    auto* start_path_state = visited.add(start_object_id, ObjectId(), ObjectId() , false, nullptr);
    auto* start_macro_state =  new MacroState(start_path_state, automaton.get_start());

    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        bool check_succeeded = false; 
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){
            check_succeeded = eval_check(start_object_id.id, *start_macro_state, t.property_checks);
        }
        if (check_succeeded&&label_matched){
            auto new_state = visited_product_graph.emplace(start_macro_state->path_state,
                                                           t.to,
                                                           start_macro_state->upper_bounds,
                                                           start_macro_state->lower_bounds,
                                                           start_macro_state->eq_vals,
                                                           start_macro_state->collected_expr);
            open.push(new_state.first.operator->());        }
    }
    delete start_macro_state;
    // insert the init state vector to the state
}

const PathState* BFSEnum::expand_neighbors(Paths::DataTest::MacroState &macroState) {
    // stop if automaton state has not outgoing transitions
    // Check if this is the first time that current_state is explored
    if (iter->at_end()) {
        current_transition = 0;
        // Check if automaton state has transitions
        if (automaton.from_to_connections[macroState.automaton_state].empty()) {
            return nullptr;
        }
        set_iter(macroState);
    }

    while (current_transition < automaton.from_to_connections[macroState.automaton_state].size()) {
        auto &transition_edge = automaton.from_to_connections[macroState.automaton_state][current_transition];
        while (iter->next()) {
            // get the edge of edge and target
            uint64_t target_id = iter->get_reached_node();

            uint64_t edge_id = iter->get_edge();
            // not allow cycle 
            if (!is_simple_path(macroState.path_state, ObjectId(iter->get_reached_node()))) {
                continue;
            }
            // progress with edges
            // edges type has checked, so we only check the properties
            // we do not progress if it is not sat with the edge transition, or the transition is not
            if ((!eval_check(edge_id, macroState, transition_edge.property_checks))) {
                continue;
            }





            // else we explore a successor transition as a node transition
            for (auto &transition_node: automaton.from_to_connections[transition_edge.to]) {
                auto label_id = QuadObjectId::get_string(transition_node.type);
                bool matched_label = match_label(target_id, label_id.id);

                bool check_value = false; 
                if (matched_label){
                   check_value =  eval_check(target_id, macroState, transition_node.property_checks);
                }
                if (matched_label && check_value) {
                    PathState* new_ptr  = visited.add(
                            ObjectId(target_id),
                            transition_edge.type_id,
                            ObjectId(edge_id),
                            transition_edge.inverse,
                            macroState.path_state
                    );
                    auto new_state = visited_product_graph.emplace(
                            new_ptr,
                            transition_node.to,
                            macroState.upper_bounds,
                            macroState.lower_bounds,
                            macroState.eq_vals,
                            macroState.collected_expr
                    );
                    if (new_state.second){
                        open.emplace(new_state.first.operator->());
                    }
                    if (automaton.decide_accept(transition_node.to)) {
                        return new_ptr;
                    }
                }
            }


        }
        current_transition++;
        if (current_transition < automaton.from_to_connections[macroState.automaton_state].size()) {
            set_iter(macroState);
        }

    }
    return nullptr;

}
bool BFSEnum::_next() {
    if (open.empty()) return false;
    // Enum if first state is final
    if (first_next) {
        const auto& current_state = open.front();

        // iterate over each macro state



        auto node_iter = provider ->node_exists(current_state-> path_state->node_id.id);
        if (!node_iter){
            open.pop();
            return false;
        }
        // start state is the solution
        if (current_state-> path_state->node_id == end_object_id && automaton.decide_accept(current_state-> automaton_state)) {
            auto path_id = path_manager.set_path(current_state -> path_state, path_var);
            parent_binding->add(path_var, path_id);
            parent_binding->add(end, current_state -> path_state->node_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(to_string(ele.second)));
            }
            queue<MacroState*> empty;
            open.swap(empty);
            return true;

        }




    }

    // iterate
    while (!open.empty()) {
        // get a new state vector
        auto &current_state = open.front();
        auto reached_final_state = expand_neighbors(*current_state);

        // Enumerate reached solutions
        if (reached_final_state != nullptr) {
            auto path_id = path_manager.set_path(reached_final_state, path_var);
            parent_binding->add(path_var, path_id);
            parent_binding->add(end, reached_final_state->node_id);
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





void BFSEnum::_reset() {
    // Empty open and visited
    queue<MacroState*> empty;
    open.swap(empty);
    visited.clear();
    visited_product_graph.clear();

    first_next = true;
    iter = make_unique<NullIndexIterator>();
    solver.reset();
    // Add starting states to open and visited
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null() , false, nullptr);

    auto* start_macro_state =  new MacroState(start_path_state, automaton.get_start());

    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        bool check_succeeded = false; 
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){
            check_succeeded = eval_check(start_object_id.id, *start_macro_state, t.property_checks);
        }
        if (check_succeeded&&label_matched){
            // the next transition should be an edge transition
            start_macro_state->automaton_state = t.to;
            auto state = visited_product_graph.insert(*start_macro_state);
            if (state.second){
                open.emplace(state.first.operator->());
            }
        }
    }
    delete start_macro_state;
    // insert the init state vector to the state
}

void BFSEnum::accept_visitor(BindingIterVisitor &visitor) {
    visitor.visit(*this);
}



