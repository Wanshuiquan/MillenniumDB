#include "bfs_enum.h"
#include "query/executor/binding_iter/paths/data_test/model/macro_state_antichain.h"

#include <cassert>

#include "query/var_id.h"
#include "query/smt/fixed_numeric_policy.h"
#include "query/smt/semantic_state_checkpoint.h"
#include "system/path_manager.h"
#include "query/smt/real/real_smt_operations.h"
using namespace Paths::DataTest::Real;

namespace {
std::string substitute_registers(const std::string& formula, const std::map<std::string, double>& reg_vals) {
    return SMT::substitute_binary64_registers(formula, reg_vals);
}

template<typename MacroState>
bool apply_reg_assigns_from_real_attrs(
        const std::map<std::tuple<std::string, ObjectId>, double>& real_attributes,
        MacroState& macro_state,
        const SMTTransition& trans)
{
    return SMT::apply_finite_binary64_register_assignments(
            real_attributes, trans, macro_state.reg_vals);
}

} // namespace

void BFSEnum::update_value(uint64_t obj) {
    for (const auto& key : attributes) {
        ObjectId key_id = std::get<1>(key);
        auto res = query_property(obj, key_id.id);
        if (res.has_value()) {
            uint64_t value_id = res.value();
            ResultReal new_value = decode_mask_real(ObjectId(value_id));
            if (std::holds_alternative<std::string>(new_value)) {
                string_attributes[key] = std::get<std::string>(new_value);
            } else if (std::holds_alternative<bool>(new_value)) {
                boolean_attributes[key] = std::get<bool>(new_value);
            } else {
                real_attributes[key] = std::get<double>(new_value);
            }
        }
    }
}

void BFSEnum::set_model(z3::solver& sat_solver) {
    auto model = get_smt_ctx().get_model(sat_solver);
    for (const auto& ele : vars) {
        std::string name = get_query_ctx().get_var_name(ele.first);
        z3::expr v = get_smt_ctx().get_var(name);
        double out = 0.0;
        auto value = model.eval(v, true);
        if (value.is_numeral(out)) {
            vars[ele.first] = out;
        }
    }
}

SMT::CheckStatus BFSEnum::check_constraints(const MacroStateReal& macro_state) {
    z3::solver sat_solver = solver;
    const auto status = macro_state.check_constraints(sat_solver, entailment_pipeline);
    if (status != SMT::CheckStatus::Sat) return status;
    set_model(sat_solver);
    get_smt_ctx().solver_pop(sat_solver);
    return status;
}

bool BFSEnum::eval_check(uint64_t obj, MacroStateReal& macro_state, const std::string& formula) {
    update_value(obj);
    exploration_depth++;

    for (const auto& ele : string_attributes) {
        std::string name = std::get<0>(ele.first);
        get_smt_ctx().add_string_var(name);
    }
    for (const auto& ele : real_attributes) {
        std::string name = std::get<0>(ele.first);
        get_smt_ctx().add_real_var(name);
    }
    for (const auto& ele : boolean_attributes) {
        std::string name = std::get<0>(ele.first);
        get_smt_ctx().add_bool_var(name);
    }
    for (const auto& ele : vars) {
        get_smt_ctx().add_real_var(get_query_ctx().get_var_name(ele.first));
    }

    auto rewritten = substitute_registers(formula, macro_state.reg_vals);
    auto property = get_smt_ctx().parse(rewritten);

    for (const auto& ele : string_attributes) {
        std::string name = std::get<0>(ele.first);
        property = get_smt_ctx().subsitute_string(name, ele.second, property);
    }
    for (const auto& ele : real_attributes) {
        std::string name = std::get<0>(ele.first);
        property = get_smt_ctx().subsitute_real(name, ele.second, property);
    }
    for (const auto& ele : boolean_attributes) {
        std::string name = std::get<0>(ele.first);
        property = get_smt_ctx().subsitute_bool(name, ele.second, property);
    }

    property = property.simplify();
    auto conjuncts = get_smt_ctx().decompose(property);
    for (const auto& conjunct : conjuncts) {
        auto normal_form = get_smt_ctx().normalizition(conjunct);
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

        if (decision == SMT::Real::AtomDecision::Inconsistent) {
            return false;
        }
    }

    return true;
}

void BFSEnum::_begin(Binding& _parent_binding) {
    parent_binding = &_parent_binding;
    first_next = true;
    iter = std::make_unique<NullIndexIterator>();
    preprocessor->begin(_parent_binding);

    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    end_object_id = (*parent_binding)[end];

    auto start_path_state = visited.add(start_object_id, ObjectId(), ObjectId(), false, nullptr);
    auto* start_macro_state = Paths::DataTest::Real::init_macro_state(start_path_state, automaton.get_start());

    update_value(start_object_id.id);
    for (auto& t : automaton.from_to_connections[automaton.get_start()]) {
        SMT::SemanticStateCheckpoint start_checkpoint(*start_macro_state);
        bool check_succeeded = false;
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched) {
            check_succeeded = apply_reg_assigns_from_real_attrs(real_attributes, *start_macro_state, t)
                           && eval_check(start_object_id.id, *start_macro_state, t.property_checks);
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
}

const PathState* BFSEnum::expand_neighbors(MacroStateReal& macro_state) {
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
            SMT::SemanticStateCheckpoint edge_checkpoint(macro_state);
            uint64_t target_id = iter->get_reached_node();
            uint64_t edge_id = iter->get_edge();

            update_value(edge_id);
            if (!apply_reg_assigns_from_real_attrs(real_attributes, macro_state, transition_edge)
                    || !eval_check(edge_id, macro_state, transition_edge.property_checks)) {
                continue;
            }

            for (auto& transition_node : automaton.from_to_connections[transition_edge.to]) {
                SMT::SemanticStateCheckpoint node_checkpoint(macro_state);
                auto label_id = QuadObjectId::get_string(transition_node.type);
                bool matched_label = match_label(target_id, label_id.id);
                bool check_value = false;
                if (matched_label) {
                    update_value(target_id);
                    check_value = apply_reg_assigns_from_real_attrs(real_attributes, macro_state, transition_node)
                               && eval_check(target_id, macro_state, transition_node.property_checks);
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
                            macro_state.collected_expr_bv,
                            macro_state.reg_vals);
                    auto inserted = visited_product_graph.emplace(next_state);
                    if (inserted.second) {
                        open.emplace(*inserted.first.operator->());
                    }

                    if (automaton.decide_accept(transition_node.to)
                        && SMT::is_satisfiable_or_throw(check_constraints(*inserted.first.operator->())))
                    {
                        return Paths::DataTest::surviving_path(inserted);
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

bool BFSEnum::_next() {
    // Run preprocessor but don't abort if it fails
    if (first_next && !preprocessor->next()) {
        first_next = false;
        std::queue<MacroStateReal> empty;
        open.swap(empty);
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
            && SMT::is_satisfiable_or_throw(check_constraints(current_state)))
        {
            auto path_id = path_manager.set_path(current_state.path_state, path_var);
            parent_binding->add(path_var, path_id);
            parent_binding->add(end, current_state.path_state->node_id);
            for (const auto& ele : vars) {
                parent_binding->add(ele.first, QuadObjectId::get_value(std::to_string(ele.second)));
            }
            std::queue<MacroStateReal> empty;
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
            parent_binding->add(end, reached_final_state->node_id);
            for (const auto& ele : vars) {
                parent_binding->add(ele.first, QuadObjectId::get_value(std::to_string(ele.second)));
            }
            return true;
        }
        open.pop();
    }

    return false;
}

void BFSEnum::_reset() {
    preprocessor->reset();
    std::queue<MacroStateReal> empty;
    open.swap(empty);
    visited.clear();
    visited_product_graph.clear();

    first_next = true;
    iter = std::make_unique<NullIndexIterator>();
    solver.reset();

    ObjectId start_object_id = start.is_var() ? (*parent_binding)[start.get_var()] : start.get_OID();
    auto start_path_state = visited.add(start_object_id, ObjectId::get_null(), ObjectId::get_null(), false, nullptr);

    auto* start_macro_state = Paths::DataTest::Real::init_macro_state(start_path_state, automaton.get_start());

    update_value(start_object_id.id);
    for (auto& t : automaton.from_to_connections[automaton.get_start()]) {
        SMT::SemanticStateCheckpoint start_checkpoint(*start_macro_state);
        bool check_succeeded = false;
        uint64_t label_id = QuadObjectId::get_string(t.type).id;
        bool label_matched = match_label(start_object_id.id, label_id);
        if (label_matched) {
            check_succeeded = apply_reg_assigns_from_real_attrs(real_attributes, *start_macro_state, t)
                           && eval_check(start_object_id.id, *start_macro_state, t.property_checks);
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
    end_object_id = (*parent_binding)[end];
}

void BFSEnum::print(std::ostream& os, int indent, bool stats) const {
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

    os << std::string(indent, ' ') << "Paths::DATA::Real::BFSEnum(path_var: " << path_var
       << ", start: " << start << ", end: " << end << ")";
    preprocessor->print(os, indent, stats);
}
