//
// Created by lhy on 9/2/24.
//
#include <cassert>

#include "bfs_enum.h"
#include "query/var_id.h"
#include "system/path_manager.h"
#include  <tuple>
using namespace std;
using namespace Paths::DataTest::LIA;

template <bool END_CHECK>
void BFSEnum<END_CHECK>::update_value(uint64_t obj) {
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
                int_attributes[key] = static_cast<int64_t>(std::get<double>(new_value));
            }
        }

    }
}

template <bool END_CHECK>
void BFSEnum<END_CHECK>::apply_reg_assigns(MacroState& macroState, const SMTTransition& trans) {
    for (const auto& [reg_name, attr_name] : trans.reg_assignments) {
        // Look up the attribute value from the current node/edge attributes
        int64_t value = 0;
        bool found = false;
        for (const auto& [key, val] : int_attributes) {
            if (std::get<0>(key) == attr_name) {
                value = val;
                found = true;
                break;
            }
        }
        if (found) {
            macroState.reg_vals[reg_name] = value;
        }
    }
}

template <bool END_CHECK>
bool BFSEnum<END_CHECK>::eval_check(uint64_t obj, MacroState& macroState, const std::string& formula) {
    // update_value
    update_value(obj);
    exploration_depth++;

    // Substitute register references in the formula string with their values
    std::string processed_formula = formula;
    for (const auto& [reg_name, reg_val] : macroState.reg_vals) {
        // Replace ??reg_name with the integer value
        std::string pattern = reg_name;
        std::string replacement = std::to_string(reg_val);
        size_t pos = 0;
        while ((pos = processed_formula.find(pattern, pos)) != std::string::npos) {
            processed_formula.replace(pos, pattern.length(), replacement);
            pos += replacement.length();
        }
    }

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

    auto property = get_smt_ctx().parse(processed_formula);
    //substitution
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
    if (END_CHECK)
    {
        return true;
    }else
    {
        return check_constraints(macroState);
    }

}

template <bool END_CHECK>
void BFSEnum<END_CHECK>::set_model(z3::solver& sat_solver, const MacroState& macroState)
{
    auto model = get_smt_ctx().get_model(sat_solver);
    for (const auto &ele:vars){
        std::string name = get_query_ctx().get_var_name(ele.first);
        z3::expr v = get_smt_ctx().get_var(name);
        // Check if this variable has a known equality value from eq_vals;
        // if so use it directly instead of extracting from the Z3 model
        auto var_ast_id = Z3_get_ast_id(v.ctx(), static_cast<Z3_ast>(v));
        auto eq_it = macroState.eq_vals.find(static_cast<int64_t>(var_ast_id));
        if (eq_it != macroState.eq_vals.end()) {
            vars[ele.first] = eq_it->second;
        } else {
            int64_t out = 0;
            auto val = model.eval(v, true);
            if (val.is_numeral_i64(out)) {
                vars[ele.first] = out;
            } else {
                vars[ele.first] = static_cast<int64_t>(val.as_double());
            }
        }
    }
}

template <bool END_CHECK>
bool BFSEnum<END_CHECK>::check_constraints(const MacroState& macroState)
{
    get_smt_ctx().solver_push(solver);
    std::set<int64_t> visited_parameter;
    int constraint_counting = 0; 
    int equality_counting = 0; 
    std::map<int64_t, int64_t> param_vals;
    auto simplify = [&constraint_counting, &param_vals, this](z3::expr formula) {
        for (auto& [id, val]: param_vals)
        {
            std::string name = get_smt_ctx().get_term(id).to_string();
            formula = get_smt_ctx().subsitute_int(name, val, formula);
        }
        auto normal_form = get_smt_ctx().normalizition(formula);
        if (normal_form.is_false())
        {
            return z3::unsat;
        } else if (normal_form.is_true())
        {
            return z3::sat;
        }
        constraint_counting ++;
        get_smt_ctx().solver_add_condition(solver, normal_form);
        return z3::unknown;
    };
    for (const auto &para: macroState.collected_expr) {
        if (visited_parameter.find(para) != visited_parameter.end()) {
            continue;
        }else {
            visited_parameter.emplace(para);
        }
        auto parameter = get_smt_ctx().get_term(para);


        if (macroState.eq_vals.find(para) != macroState.eq_vals.end()) {
            // Optimization: if the LHS is a single variable, the equality value
            // is already tracked by update_bound for contradiction detection.
            // Skip adding to Z3 to avoid solver calls; set_model will use eq_vals directly.
            if (parameter.is_const()) {
                // Single variable equality: handled by set_model from eq_vals
                int64_t val = macroState.eq_vals.at(para);
                get_smt_ctx().solver_add_condition(solver, parameter == get_smt_ctx().add_int_val(static_cast<int>(val)));
                equality_counting++; 
                constraint_counting++;
                param_vals[para] = val;

            } else {
                int64_t val = macroState.eq_vals.at(para);
                get_smt_ctx().solver_add_condition(solver, parameter == get_smt_ctx().add_int_val(static_cast<int>(val)));
                constraint_counting++;
            } 
        }

        if (macroState.upper_bounds.find(para) != macroState.upper_bounds.end()) {
            int64_t val = macroState.upper_bounds.at(para);
            auto formula = parameter <= get_smt_ctx().add_int_val(static_cast<int>(val));
            auto res = simplify(formula);
            if (res == z3::unsat)
            {
                return false;
            }
            if (res == z3::sat)
            {
                return true;
            }
        }

        if (macroState.lower_bounds.find(para) != macroState.lower_bounds.end()) {
            int64_t val = macroState.lower_bounds.at(para);
            auto formula = parameter >= get_smt_ctx().add_int_val(static_cast<int>(val));
            auto res = simplify(formula);
            if (res == z3::unsat)
            {
                return false;
            }
            if (res == z3::sat)
            {
                return true;
            }
        }

        if (macroState.neq_vals.find(para) != macroState.neq_vals.end()) {
            for (const auto& val : macroState.neq_vals.at(para)) {
                auto formula = parameter != get_smt_ctx().add_int_val(static_cast<int>(val));
                auto res = simplify(formula);
                if (res == z3::unsat)
                {
                    return false;
                }
                if (res == z3::sat)
                {
                    return true;
                }
            }
        }

        if (macroState.gt_vals.find(para) != macroState.gt_vals.end()) {
            int64_t val = macroState.gt_vals.at(para);
            auto formula = parameter > get_smt_ctx().add_int_val(static_cast<int>(val));
            auto res = simplify(formula);
            if (res == z3::unsat)
            {
                return false;
            }
            if (res == z3::sat)
            {
                return true;
            }
        }

        if (macroState.lt_vals.find(para) != macroState.lt_vals.end()) {
            int64_t val = macroState.lt_vals.at(para);
            auto formula = parameter < get_smt_ctx().add_int_val(static_cast<int>(val));
            auto res = simplify(formula);
            if (res == z3::unsat)
            {
                return false;
            }
            if (res == z3::sat)
            {
                return true;
            }
        }

    }

    if (equality_counting == constraint_counting)
    {
        // Populate vars from eq_vals (bypassing Z3 solver since all constraints are equalities)
        for (const auto &ele : vars) {
            std::string name = get_query_ctx().get_var_name(ele.first);
            z3::expr v = get_smt_ctx().get_var(name);
            auto var_ast_id = Z3_get_ast_id(v.ctx(), static_cast<Z3_ast>(v));
            auto eq_it = macroState.eq_vals.find(static_cast<int64_t>(var_ast_id));
            if (eq_it != macroState.eq_vals.end()) {
                vars[ele.first] = eq_it->second;
            }
        }
        get_smt_ctx().solver_pop(solver);
        return true;
    }
    switch (get_smt_ctx().check(solver)) {
    case z3::sat: {
            set_model(solver, macroState);
            get_smt_ctx().solver_pop(solver);
            assert(solver.assertions().empty());
            return true;
    }
    case z3::unsat: {
            get_smt_ctx().solver_pop(solver);
            return false;
    }
    case z3::unknown:{
            get_smt_ctx().solver_pop(solver);
            return false;
    }
    }
    return false;
}

template <bool END_CHECK>
void BFSEnum<END_CHECK>::_begin(Binding& _parent_binding) {
    parent_binding = &_parent_binding;
    first_next = true;
    iter = make_unique<NullIndexIterator>();
    edge_buffer.clear();
    edge_buffer_pos = 0;
    preprocessor ->begin(_parent_binding);
    // Init start object id
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();

    // Store ID for end object
    // init the start node
    auto* start_path_state = visited.add(start_object_id, ObjectId(), ObjectId() , false, nullptr);
    auto* start_macro_state = init_macro_state(start_path_state, automaton.get_start());

    // Populate attributes for the start node (needed for register assignments)
    update_value(start_object_id.id);

    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        bool check_succeeded = false; 
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){
            apply_reg_assigns(*start_macro_state, t);
            check_succeeded = eval_check(start_object_id.id, *start_macro_state, t.property_checks);
        }
        if (check_succeeded){
            start_macro_state->automaton_state = t.to;
            auto new_state = visited_product_graph.emplace(copy_macro_state(*start_macro_state));
            if (new_state.second) {
                open.emplace(new_state.first.operator*());
            }
        }
    }
    delete start_macro_state;
    // insert the init state vector to the state
}

template <bool END_CHECK>
const PathState* BFSEnum<END_CHECK>::expand_neighbors(MacroState& macroState) {
    // Detect if we are processing a new state by checking if the
    // current_transition is out of range for this automaton state.
    // If so, the buffer/iterator is stale and must be reset.
    if (current_transition >= automaton.from_to_connections[macroState.automaton_state].size()) {
        current_transition = 0;
        edge_buffer.clear();
        edge_buffer_pos = 0;
    }
    
    // Handle buffer resumption: when a solution was found on a previous call
    // before the buffer was exhausted, we need to continue with the next transition.
    if (!edge_buffer.empty() && edge_buffer_pos >= edge_buffer.size()) {
        edge_buffer.clear();
        edge_buffer_pos = 0;
        current_transition++;
        if (current_transition < automaton.from_to_connections[macroState.automaton_state].size()) {
            set_iter(macroState);
            // Batch-load all edges for the next transition
            while (iter->next()) {
                edge_buffer.emplace_back(iter->get_reached_node(), iter->get_edge());
            }
        } else {
            return nullptr;
        }
    }

    // stop if automaton state has not outgoing transitions
    // Check if this is the first time that current_state is explored
    if (iter->at_end() && edge_buffer.empty()) {
        current_transition = 0;
        // Check if automaton state has transitions
        if (automaton.from_to_connections[macroState.automaton_state].empty()) {
            return nullptr;
        }
        set_iter(macroState);
        // Batch-load all edges for the first transition into the buffer
        while (iter->next()) {
            edge_buffer.emplace_back(iter->get_reached_node(), iter->get_edge());
        }
    }

    while (current_transition < automaton.from_to_connections[macroState.automaton_state].size()) {
        auto &transition_edge = automaton.from_to_connections[macroState.automaton_state][current_transition];

        // Process from buffer (may have been partially consumed from a previous call)
        while (edge_buffer_pos < edge_buffer.size()) {
            auto [target_id, edge_id] = edge_buffer[edge_buffer_pos++];

            // progress with edges
            // edges type has checked, so we only check the properties
            // Update attributes for the edge before capturing register values
            update_value(edge_id);
            apply_reg_assigns(macroState, transition_edge);
            if ((!eval_check(edge_id, macroState, transition_edge.property_checks))) {
                continue;
            }

            // else we explore a successor transition as a node transition
            for (auto &transition_node: automaton.from_to_connections[transition_edge.to]) {
                auto label_id = QuadObjectId::get_string(transition_node.type);
                bool matched_label = match_label(target_id, label_id.id);

                bool check_value = false; 
                if (matched_label){                  // Update attributes for the target node before capturing register values
                  update_value(target_id);                   apply_reg_assigns(macroState, transition_node);
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
                            init_macro_state_with_data(
                            new_ptr,
                            transition_node.to,
                            macroState.upper_bounds,
                            macroState.lower_bounds,
                            macroState.eq_vals,
                            macroState.gt_vals,
                            macroState.lt_vals,
                            macroState.neq_vals,
                            macroState.collected_expr,
                            macroState.reg_vals)
                    );
                    if (new_state.second){
                        open.emplace(new_state.first.operator*());
                    }
                    if (automaton.decide_accept(transition_node.to) && check_constraints(*new_state.first.operator->())) {
                        return new_ptr;
                    }
                }
            }
        }

        // Buffer for this transition exhausted, move to next transition
        current_transition++;
        if (current_transition < automaton.from_to_connections[macroState.automaton_state].size()) {
            set_iter(macroState);
            // Batch-load all edges for the next transition
            edge_buffer.clear();
            edge_buffer_pos = 0;
            while (iter->next()) {
                edge_buffer.emplace_back(iter->get_reached_node(), iter->get_edge());
            }
        }
    }
    return nullptr;
}
template <bool END_CHECK>
bool BFSEnum<END_CHECK>::_next() {
    // Run preprocessor but don't abort if it fails — the main BFS should still try
    preprocessor->next();
    if (open.empty()) return false;
    // Enum if first state is final
    if (first_next) {
        const auto& current_state = open.front();

        // iterate over each macro state



        auto node_iter = provider ->node_exists(current_state. path_state->node_id.id);
        if (!node_iter){
            open.pop();
            return false;
        }
        // start state is the solution
        if (current_state. path_state->node_id == end_object_id && automaton.decide_accept(current_state. automaton_state)) {
            auto path_id = path_manager.set_path(current_state . path_state, path_var);
            parent_binding->add(path_var, path_id);
            parent_binding->add(end, current_state. path_state->node_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(std::to_string(ele.second)));
            }
            std::queue<MacroState> empty;
            open.swap(empty);
            return true;
        }

    }

    // iterate
    while (!open.empty()) {
        auto& current_state = open.front();
        auto reached_final_state = expand_neighbors(current_state);

        // Enumerate reached solutions
        if (reached_final_state != nullptr) {
            auto path_id = path_manager.set_path(reached_final_state, path_var);
            parent_binding->add(path_var, path_id);
            parent_binding->add(end, reached_final_state->node_id);
            for (const auto& ele: vars){
                parent_binding->add(ele.first, QuadObjectId::get_value(std::to_string(ele.second)));
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
void BFSEnum<END_CHECK>::_reset() {
    // Empty open and visited
    preprocessor->reset();
    std::queue<MacroState> empty;
    open.swap(empty);
    visited_product_graph.clear();
    visited.clear();

    first_next = true;
    iter = make_unique<NullIndexIterator>();
    edge_buffer.clear();
    edge_buffer_pos = 0;
    solver.reset();
    // Add starting states to open and visited
    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null() , false, nullptr);

    auto* start_macro_state = init_macro_state(start_path_state, automaton.get_start());

    // Populate attributes for the start node (needed for register assignments)
    update_value(start_object_id.id);

    // explore from the init state
    for (auto& t: automaton.from_to_connections[automaton.get_start()]){
        // check_property
        bool check_succeeded = false; 
        //check_label
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched){
            apply_reg_assigns(*start_macro_state, t);
            check_succeeded = eval_check(start_object_id.id, *start_macro_state, t.property_checks);
        }
        if (check_succeeded){
            start_macro_state->automaton_state = t.to;
            auto new_state = visited_product_graph.emplace(copy_macro_state(*start_macro_state));
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

    get_smt_ctx().solver_reset(solver);
}

template <bool END_CHECK>
void BFSEnum<END_CHECK>::print(std::ostream& os, int indent, bool stats) const {
    for (int i = 0; i < indent; ++i) {
        os << ' ';
    }
    os << "BFSEnumLIA(";
    os << "path_var: " << path_var;
    os << ", start: " << start;
    os << ", end: " << end;
    os << ", automaton: " << automaton.get_total_states();
    os << ")";
}

template class Paths::DataTest::LIA::BFSEnum<true>;
template class Paths::DataTest::LIA::BFSEnum<false>;
