#include "bfs_check.h"

#include <optional>

#include "query/var_id.h"
#include "system/path_manager.h"

using namespace Paths::DataTest::Integer;

template<bool END_CHECK>
void BFSCheck<END_CHECK>::update_value(uint64_t obj) {
    for (const auto& key : attributes) {
        ObjectId key_id = std::get<1>(key);
        auto res = query_property(obj, key_id.id);
        if (res.has_value()) {
            uint64_t value_id = res.value();
            Result new_value = decode_mask(ObjectId(value_id));
            if (std::holds_alternative<std::string>(new_value)) {
                string_attributes[key] = std::get<std::string>(new_value);
            } else if (std::holds_alternative<bool>(new_value)) {
                boolean_attributes[key] = std::get<bool>(new_value);
            } else {
                int_attributes[key] = static_cast<int64_t>(std::get<double>(new_value));
            }
        }
    }
}

template<bool END_CHECK>
void BFSCheck<END_CHECK>::set_model(z3::solver& sat_solver) {
    auto model = get_smt_ctx().get_model(sat_solver);
    for (const auto& ele : vars) {
        std::string name = get_query_ctx().get_var_name(ele.first);
        z3::expr v = get_smt_ctx().get_var(name);
        int64_t out = 0;
        auto value = model.eval(v, true);
        if (value.is_numeral_i64(out)) {
            vars[ele.first] = out;
        }
    }
}

template<bool END_CHECK>
bool BFSCheck<END_CHECK>::check_constraints(const MacroStateInt& macro_state) {
    get_smt_ctx().solver_push(solver);
    for (const auto& atom : macro_state.collected_expr_int) {
        get_smt_ctx().solver_add_condition(solver, atom);
    }

    switch (get_smt_ctx().check(solver)) {
    case z3::sat:
        set_model(solver);
        get_smt_ctx().solver_pop(solver);
        return true;
    case z3::unsat:
    case z3::unknown:
        get_smt_ctx().solver_pop(solver);
        return false;
    }
    get_smt_ctx().solver_pop(solver);
    return false;
}

template<bool END_CHECK>
bool BFSCheck<END_CHECK>::eval_check(uint64_t obj, MacroStateInt& macro_state, const std::string& formula) {
    update_value(obj);
    exploration_depth++;

    for (const auto& ele : string_attributes) {
        std::string name = std::get<0>(ele.first);
        get_smt_ctx().add_string_var(name);
    }
    for (const auto& ele : int_attributes) {
        std::string name = std::get<0>(ele.first);
        get_smt_ctx().add_int_var(name);
    }
    for (const auto& ele : boolean_attributes) {
        std::string name = std::get<0>(ele.first);
        get_smt_ctx().add_bool_var(name);
    }
    for (const auto& ele : vars) {
        get_smt_ctx().add_int_var(get_query_ctx().get_var_name(ele.first));
    }

    auto rewritten = SMT::Int::AbstractRewriter64::rewrite_lra_formula_to_int(formula);
    auto property = get_smt_ctx().parse(rewritten);

    for (const auto& ele : string_attributes) {
        std::string name = std::get<0>(ele.first);
        property = get_smt_ctx().subsitute_string(name, ele.second, property);
    }
    for (const auto& ele : int_attributes) {
        std::string name = std::get<0>(ele.first);
        property = get_smt_ctx().subsitute_int(name, ele.second, property);
    }
    for (const auto& ele : boolean_attributes) {
        std::string name = std::get<0>(ele.first);
        property = get_smt_ctx().subsitute_bool(name, ele.second, property);
    }

    auto conjuncts = get_smt_ctx().decompose(property);
    for (const auto& c : conjuncts) {
        auto normal_form = get_smt_ctx().normalizition(c);
        if (normal_form.is_true()) {
            continue;
        }
        if (normal_form.is_false()) {
            return false;
        }

        auto decision = entailment_pipeline.evaluate_and_update(
                macro_state.collected_expr_bv,
                macro_state.collected_expr_int,
                normal_form);

        if (decision == SMT::Int::AtomDecision::Inconsistent) {
            return false;
        }
    }

    if constexpr (END_CHECK) {
        return true;
    }
    return check_constraints(macro_state);
}

template<bool END_CHECK>
void BFSCheck<END_CHECK>::_begin(Binding& _parent_binding) {
    parent_binding = &_parent_binding;
    preprocessor->begin(_parent_binding);
    first_next = true;
    iter = std::make_unique<NullIndexIterator>();

    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    end_object_id = end.is_var() ? (*parent_binding)[end.get_var()] : end.get_OID();

    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null(), false, nullptr);
    auto start_macro_state = init_macro_state(start_path_state, automaton.get_start());

    for (auto& t : automaton.from_to_connections[automaton.get_start()]) {
        bool check_succeeded = false;
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched) {
            check_succeeded = eval_check(start_object_id.id, *start_macro_state, t.property_checks);
        }
        if (check_succeeded) {
            start_macro_state->automaton_state = t.to;
            auto next_state = init_macro_state_with_data(
                    start_macro_state->path_state,
                    t.to,
                    start_macro_state->collected_expr_int,
                    start_macro_state->collected_expr_bv);
            auto inserted = visited_product_graph.emplace(next_state);
            if (inserted.second) {
                open.emplace(*inserted.first.operator->());
            }
        }
    }
    delete start_macro_state;
}

template<bool END_CHECK>
const PathState* BFSCheck<END_CHECK>::expand_neighbors(MacroStateInt& macro_state) {
    if (iter->at_end()) {
        current_transition = 0;
        if (automaton.from_to_connections[macro_state.automaton_state].empty()) {
            return nullptr;
        }
        set_iter(macro_state);
    }

    while (current_transition < automaton.from_to_connections[macro_state.automaton_state].size()) {
        auto& transition_edge = automaton.from_to_connections[macro_state.automaton_state][current_transition];
        while (iter->next()) {
            uint64_t edge_id = iter->get_edge();
            uint64_t target_id = iter->get_reached_node();

            if (!is_simple_path(macro_state.path_state, ObjectId(target_id))) {
                continue;
            }

            if (!eval_check(edge_id, macro_state, transition_edge.property_checks)) {
                continue;
            }

            for (auto& transition_node : automaton.from_to_connections[transition_edge.to]) {
                auto label_id = QuadObjectId::get_string(transition_node.type);
                bool matched_label = match_label(target_id, label_id.id);
                bool check_value = false;
                if (matched_label) {
                    check_value = eval_check(target_id, macro_state, transition_node.property_checks);
                }

                if (matched_label && check_value) {
                    PathState* new_ptr = visited.add(
                            ObjectId(target_id),
                            transition_edge.type_id,
                            ObjectId(edge_id),
                            transition_edge.inverse,
                            macro_state.path_state);

                    auto next_state = init_macro_state_with_data(
                            new_ptr,
                            transition_node.to,
                            macro_state.collected_expr_int,
                            macro_state.collected_expr_bv);
                    auto inserted = visited_product_graph.emplace(next_state);
                    if (inserted.second) {
                        open.emplace(*inserted.first.operator->());
                    }

                    if (automaton.decide_accept(transition_node.to) && target_id == end_object_id.id) {
                        return new_ptr;
                    }
                }
            }
        }

        current_transition++;
        if (current_transition < automaton.from_to_connections[macro_state.automaton_state].size()) {
            set_iter(macro_state);
        }
    }

    return nullptr;
}

template<bool END_CHECK>
bool BFSCheck<END_CHECK>::_next() {
    if (!preprocessor->next()) {
        return false;
    }

    if (open.empty()) {
        return false;
    }

    if (first_next) {
        first_next = false;
        const auto& current_state = open.front();

        auto node_iter = provider->node_exists(current_state.path_state->node_id.id);
        if (!node_iter) {
            open.pop();
            return false;
        }

        if (current_state.path_state->node_id == end_object_id
            && automaton.decide_accept(current_state.automaton_state)
            && check_constraints(current_state))
        {
            auto path_id = path_manager.set_path(current_state.path_state, path_var);
            parent_binding->add(path_var, path_id);
            for (const auto& ele : vars) {
                parent_binding->add(ele.first, QuadObjectId::get_value(std::to_string(ele.second)));
            }
            std::queue<MacroStateInt> empty;
            open.swap(empty);
            return true;
        }
    }

    while (!open.empty()) {
        auto& current_state = open.front();
        auto reached_final_state = expand_neighbors(current_state);

        if (reached_final_state != nullptr) {
            auto path_id = path_manager.set_path(reached_final_state, path_var);
            parent_binding->add(path_var, path_id);
            for (const auto& ele : vars) {
                parent_binding->add(ele.first, QuadObjectId::get_value(std::to_string(ele.second)));
            }
            return true;
        }
        open.pop();
    }

    return false;
}

template<bool END_CHECK>
void BFSCheck<END_CHECK>::_reset() {
    preprocessor->reset();
    std::queue<MacroStateInt> empty;
    open.swap(empty);
    visited.clear();
    visited_product_graph.clear();

    first_next = true;
    iter = std::make_unique<NullIndexIterator>();
    solver.reset();

    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null(), false, nullptr);
    auto* start_macro_state = init_macro_state(start_path_state, automaton.get_start());

    for (auto& t : automaton.from_to_connections[automaton.get_start()]) {
        bool check_succeeded = false;
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched) {
            check_succeeded = eval_check(start_object_id.id, *start_macro_state, t.property_checks);
        }
        if (check_succeeded) {
            start_macro_state->automaton_state = t.to;
            auto inserted = visited_product_graph.emplace(copy_macro_state(*start_macro_state));
            if (inserted.second) {
                open.emplace(*inserted.first.operator->());
            }
        }
    }

    delete start_macro_state;
    end_object_id = end.is_var() ? (*parent_binding)[end.get_var()] : end.get_OID();
}

template<bool END_CHECK>
void BFSCheck<END_CHECK>::print(std::ostream& os, int indent, bool stats) const {
    if (stats) {
        auto memory_consumption = Z3_get_estimated_alloc_size() / (1024 * 1024);
        auto smt_operation_time = get_smt_ctx().get_other_run_time() / (1e6);
        auto smt_solver_time = get_smt_ctx().get_solver_run_time() / (1e6);

        os << std::string(indent, ' ') << "[begin: " << stat_begin << " next: " << stat_next
           << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches
           << " solver_memory_consumption: " << memory_consumption << " MB "
           << " z3_operation_time: " << smt_operation_time << " ms "
           << " z3_solver_time: " << smt_solver_time << " ms "
           << " exploration_depth: " << exploration_depth
           << "]\n";
    }

    os << std::string(indent, ' ') << "Paths::DATA::Integer::BFSCheck(path_var: " << path_var
       << ", start: " << start << ", end: " << end << ")\n";
}

template class Paths::DataTest::Integer::BFSCheck<true>;
template class Paths::DataTest::Integer::BFSCheck<false>;
