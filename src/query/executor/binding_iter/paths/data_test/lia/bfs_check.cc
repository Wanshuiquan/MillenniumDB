//
// Created by lhy on 9/2/24.
//
#include <optional>

#include "bfs_check.h"

#include "query/var_id.h"
#include "system/path_manager.h"
using namespace std;
using namespace Paths::DataTest::LIA;

template <bool END_CHECK>
void BFSCheck<END_CHECK>::update_value(uint64_t obj) {
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
                int_attributes[key] = static_cast<int64_t>(std::get<double>(new_value));
            }
        }
    }
}

template <bool END_CHECK>
bool BFSCheck<END_CHECK>::eval_check(uint64_t obj, MacroState& macroState, const std::string& formula) {
    // update_value
    update_value(obj);
    exploration_depth++;
    // Initialize context
    for (const auto& ele: string_attributes){
        auto attr =  ele.first;
        std::string name = std::get<0>(attr);
        get_smt_ctx().add_string_var(name);
    }
    for (const auto& ele: int_attributes){
        auto attr =  ele.first;
        std::string name = std::get<0>(attr);
        get_smt_ctx().add_int_var(name);
    }
    for (const auto& ele: boolean_attributes){
        auto attr =  ele.first;
        std::string name = std::get<0>(attr);
        get_smt_ctx().add_bool_var(name);
    }
    for (const auto& ele: vars){
        auto var =  ele.first;
        get_smt_ctx().add_int_var(get_query_ctx().get_var_name(var));
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

    for (const auto& ele: int_attributes) {
        auto attr = ele.first;
        std::string name = std::get<0>(attr);
        int64_t value = ele.second;
        property = get_smt_ctx().subsitute_int(name, value, property);
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
    if (! END_CHECK)
    {
        get_smt_ctx().solver_push(s);
        //check the sat for the current bound
        std::set<int64_t> visited_parameter;
        for (const auto& para: macroState.collected_expr){
            if (visited_parameter.find(para) != visited_parameter.end()) {
                continue;
            }else {
                visited_parameter.emplace(para);
            }
            auto parameter = get_smt_ctx().get_term(para);
            if (macroState.upper_bounds.find(para) != macroState.upper_bounds.end()){
                int64_t val = macroState.upper_bounds.at(para);
                get_smt_ctx().solver_add_condition(s, parameter <= get_smt_ctx().add_int_val(static_cast<int>(val)));
            }
            if (macroState.lower_bounds.find(para) != macroState.lower_bounds.end()){
                int64_t val = macroState.lower_bounds.at(para);
                get_smt_ctx().solver_add_condition(s, parameter >= get_smt_ctx().add_int_val(static_cast<int>(val)));
            }
            if (macroState.eq_vals.find(para) != macroState.eq_vals.end()){
                int64_t val = macroState.eq_vals.at(para);
                get_smt_ctx().solver_add_condition(s, parameter == get_smt_ctx().add_int_val(static_cast<int>(val)));
            }
            if (macroState.gt_vals.find(para) != macroState.gt_vals.end()){
                int64_t val = macroState.gt_vals.at(para);
                get_smt_ctx().solver_add_condition(s, parameter > get_smt_ctx().add_int_val(static_cast<int>(val)));
            }
            if (macroState.lt_vals.find(para) != macroState.lt_vals.end()){
                int64_t val = macroState.lt_vals.at(para);
                get_smt_ctx().solver_add_condition(s, parameter < get_smt_ctx().add_int_val(static_cast<int>(val)));
            }
            if (macroState.neq_vals.find(para) != macroState.neq_vals.end()){
                for (const auto& val : macroState.neq_vals.at(para)) {
                    get_smt_ctx().solver_add_condition(s, parameter != get_smt_ctx().add_int_val(static_cast<int>(val)));
                }
            }
        }



        switch (s.check()) {
        case z3::sat: {
                auto model = get_smt_ctx().get_model(s);
                for (const auto &ele:vars){
                    std::string name = get_query_ctx().get_var_name(ele.first);
                    z3::expr v = get_smt_ctx().get_var(name);
                    auto val = model.eval(v, true);
                    int64_t out = 0;
                    if (val.is_numeral_i64(out)) {
                        vars[ele.first] = out;
                    } else {
                        vars[ele.first] = static_cast<int64_t>(val.as_double());
                    }
                }
                get_smt_ctx().solver_pop(s);
                return true;
        }
        case z3::unsat: get_smt_ctx().solver_pop(s);return false;
        case z3::unknown: get_smt_ctx().solver_pop(s); return false;
        }
    }
     return true;
}

template <bool END_CHECK>
void BFSCheck<END_CHECK>::_begin(Binding& _parent_binding) {
    parent_binding = &_parent_binding;
     preprocessor->begin(_parent_binding);
    first_next = true;
    iter = make_unique<NullIndexIterator>();

    // Init start object id
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();

    // Store ID for end object
    end_object_id = end.is_var() ? (*parent_binding)[end.get_var()] : end.get_OID();
    // init the start node
    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null() , false, nullptr);
    auto start_macro_state =  init_macro_state(start_path_state, automaton.get_start());

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
        if (check_succeeded){
            start_macro_state->automaton_state = t.to;
            auto novi_state = init_macro_state_with_data(
                    start_macro_state->path_state,
                    t.to,
                    start_macro_state->upper_bounds,
                    start_macro_state->lower_bounds,
                    start_macro_state->eq_vals,
                    start_macro_state->gt_vals,
                    start_macro_state->lt_vals,
                    start_macro_state->neq_vals,
                    start_macro_state->collected_expr
                    );
            auto new_state = visited_product_graph.emplace(novi_state);
            if (new_state.second) {
                open.emplace(new_state.first.operator*());
            }

        }
    }
    delete start_macro_state;
    // insert the init state vector to the state
}


template <bool END_CHECK>
const PathState* BFSCheck<END_CHECK>::expand_neighbors(MacroState& macroState){
    // stop if automaton state has not outgoing transitions
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
            uint64_t edge_id = iter->get_edge();
            uint64_t target_id = iter->get_reached_node();
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
                  check_value=    eval_check(target_id, macroState, transition_node.property_checks);
                }
                if (matched_label && check_value) {

                    PathState* new_ptr  = visited.add(
                            ObjectId(target_id),
                            transition_edge.type_id,
                            ObjectId(edge_id),
                            transition_edge.inverse,
                            macroState.path_state
                    );


                    auto novi_state = init_macro_state_with_data(
                            new_ptr,
                            transition_node.to,
                            macroState.upper_bounds,
                            macroState.lower_bounds,
                            macroState.eq_vals,
                            macroState.gt_vals,
                            macroState.lt_vals,
                            macroState.neq_vals,
                            macroState.collected_expr
                            );
                    auto new_state = visited_product_graph.emplace(novi_state);
                    if (new_state.second) {
                        open.emplace(new_state.first.operator*());
                    }

                    if (automaton.decide_accept(transition_node.to) && target_id == end_object_id.id) {
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
template <bool END_CHECK>
bool BFSCheck<END_CHECK>::_next() {
     if (!preprocessor->next()) {
         return false;
     }
    // Check if first state is final
    if (first_next) {
        const auto& current_state = open.front();

        // iterate over each macro state



        auto node_iter = provider ->node_exists(current_state.path_state->node_id.id);
        if (!node_iter){
            open.pop();
            return false;
        }
        // start state is the solution
        if (current_state. path_state->node_id == end_object_id && automaton.decide_accept(current_state.automaton_state)) {
            auto path_id = path_manager.set_path(current_state.path_state, path_var);
            parent_binding->add(path_var, path_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(to_string(ele.second)));
            }
            queue<MacroState > empty;
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
        if (reached_final_state != nullptr) {
            auto path_id = path_manager.set_path(reached_final_state, path_var);
            parent_binding->add(path_var, path_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(to_string(ele.second)));
            }
            return true;
        } else {
            // Pop and visit next in queue
            open.pop();
        }
    }
    return false;
}


template <bool END_CHECK>
void BFSCheck<END_CHECK>::_reset() {
     preprocessor->reset();
    // Empty open and visited
    std::queue<MacroState> empty;
    open.swap(empty);
    visited_product_graph.clear();
    visited.clear();
    first_next = true;
    iter = make_unique<NullIndexIterator>();

    // Add starting states to open and visited
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null() , false, nullptr);

    auto* start_macro_state =  init_macro_state(start_path_state, automaton.get_start());

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
        if (check_succeeded){
            start_macro_state->automaton_state = t.to;
            auto novi_state = init_macro_state_with_data(
                    start_macro_state->path_state,
                    t.to,
                    start_macro_state->upper_bounds,
                    start_macro_state->lower_bounds,
                    start_macro_state->eq_vals,
                    start_macro_state->gt_vals,
                    start_macro_state->lt_vals,
                    start_macro_state->neq_vals,
                    start_macro_state->collected_expr
                    );
            auto new_state = visited_product_graph.emplace(novi_state);
            if (new_state.second) {
                open.emplace(new_state.first.operator*());
            }
        }
    }
    delete start_macro_state;

    for (auto& ele: vars){
        ele.second = 0;
    }
    string_attributes.clear();
    int_attributes.clear();
    boolean_attributes.clear();

    get_smt_ctx().solver_reset(s);
}

template <bool END_CHECK>
void BFSCheck<END_CHECK>::print(std::ostream& os, int indent, bool stats) const {
    for (int i = 0; i < indent; ++i) {
        os << ' ';
    }
    os << "BFSCheckLIA(";
    os << "path_var: " << path_var;
    os << ", start: " << start;
    os << ", end: " << end;
    os << ", automaton: " << automaton.get_total_states();
    os << ")";
}


template class Paths::DataTest::LIA::BFSCheck<true>;
template class Paths::DataTest::LIA::BFSCheck<false>;
