//
// Created by lhy on 3/14/26.
//

#include "constraint_path_plan.h"
#include "graph_models/quad_model/quad_model.h"
#include "graph_models/quad_model/quad_object_id.h"
#include "query/exceptions.h"
#include "query/executor/binding_iter/paths/data_test/bfs_check.h"
#include "query/executor/binding_iter/paths/data_test/bfs_enum.h"
#include "query/executor/binding_iter/paths/data_test/experimental/naive_bfs_check.h"
#include "query/executor/binding_iter/paths/data_test/experimental/naive_bfs_enum.h"
#include "query/executor/binding_iter/paths/smt_unfixed_composite.h"
#include "query/executor/binding_iter/paths/index_provider/quad_model_index_provider.h"

#include "query/query_context.h"
using namespace MQL;
using namespace std;
using namespace Paths;

ConstraintPathPlan::ConstraintPathPlan(
        std::vector<bool>& begin_at_left,
        Path::Direction direction,
        VarId path_var,
        Id from,
        Id to,
        RegularPathExpr& path,
        PathSemantic path_semantic,
        uint64_t K
) :
        begin_at_left(begin_at_left),
        direction(direction),
        path_var(path_var),
        from(from),
        to(to),
        path(path),
        K(K),
        from_assigned(from.is_OID()),
        to_assigned(to.is_OID()),
        path_semantic(path_semantic) {
    if (path_semantic == PathSemantic::DATA_TEST) {
        smt_automaton = path.get_smt_automaton(&QuadObjectId::get_named_node);
        auto inverted_path = path.clone()->invert();
        smt_inverted = inverted_path->get_smt_automaton(&QuadObjectId::get_named_node);
    } else if (path_semantic == PathSemantic::NAIVE_DATA_TEST) {
        smt_automaton = path.get_smt_automaton(&QuadObjectId::get_named_node);
        auto inverted_path = path.clone()->invert();
        smt_inverted = inverted_path->get_smt_automaton(&QuadObjectId::get_named_node);
    }
}

double ConstraintPathPlan::estimate_cost() const
{
    // TODO: find a better estimation
    if (!to_assigned && !from_assigned) {
        return std::numeric_limits<double>::max();
    }
    return /*100.0 +*/ estimate_output_size();
}
double ConstraintPathPlan::estimate_output_size() const
{
    // TODO: find a better estimation
    const double total_connections = quad_model.catalog.edge_count();
    return total_connections * total_connections;
}


void ConstraintPathPlan::print(std::ostream& os, int indent) const
{
    for (int i = 0; i < indent; ++i) {
        os << ' ';
    }
    os << "PathPlan(";
    os << "from: " << from;
    os << ", to: " << to;
    os << ", path: " << path_var << ": " << path.to_string();
    os << ")";

    os << ",\n";
    for (int i = 0; i < indent; ++i) {
        os << ' ';
    }
    os << "  ↳ Estimated factor: " << estimate_output_size();
}

std::set<VarId> ConstraintPathPlan::get_vars() const
{
    std::set<VarId> result;
    if (from.is_var() && !from_assigned) {
        result.insert(from.get_var());
    }
    if (to.is_var() && !to_assigned) {
        result.insert(to.get_var());
    }
  // need to implement for PA
    return result;
}

void ConstraintPathPlan::set_input_vars(const std::set<VarId>& input_vars)
{
    set_input_var(input_vars, from, &from_assigned);
    set_input_var(input_vars, to, &to_assigned);
}



unique_ptr<Paths::IndexProvider> ConstraintPathPlan::get_provider(const SMTAutomaton& automaton) const {
    auto t_info = unordered_map<uint64_t, Paths::IndexType>();
    auto t_inv_info = unordered_map<uint64_t, Paths::IndexType>();
    for (size_t state = 0; state < automaton.from_to_connections.size(); state++) {
        for (auto& transition : automaton.from_to_connections[state]) {
            if (transition.inverse) {
                // Avoid transitions that are already stored
                if (t_inv_info.find(transition.type_id.id) != t_inv_info.end()) {
                    continue;
                }
                t_inv_info.insert({transition.type_id.id, Paths::IndexType::BTREE});

            } else {
                // Avoid transitions that are already stored
                if (t_info.find(transition.type_id.id) != t_info.end()) {
                    continue;
                }
                t_info.insert({transition.type_id.id, Paths::IndexType::BTREE});
            }
        }
    }
    return make_unique<Paths::QuadModelIndexProvider>(std::move(t_info),
                                                      std::move(t_inv_info),
                                                      &get_query_ctx().thread_info.interruption_requested);
}

std::unique_ptr<BindingIter> ConstraintPathPlan::get_check(const SMTAutomaton& automaton, Id start, Id end) const {
    auto provider = get_provider(automaton);
    auto help_provider = get_provider(automaton);
    auto  helper = std::make_unique<Paths::DataTest::PreCheck>(start, end, automaton, std::move(help_provider));
    if(path_semantic == PathSemantic::DATA_TEST){
        return make_unique<Paths::DataTest::BFSCheck<true>>(path_var, start, end, automaton, std::move(provider), std::move(helper));
    }
    else{
        return make_unique<Paths::DataTest::Naive::NaiveBFSCheck>(path_var, start, end, automaton, std::move(provider));
    }

}

std::unique_ptr<BindingIter> ConstraintPathPlan::get_enum(const SMTAutomaton& automaton, Id start, VarId end) const {
    auto provider = get_provider(automaton);
    auto help_provider = get_provider(automaton);
    auto  helper = std::make_unique<Paths::DataTest::PreEnum>(start, automaton, std::move(help_provider));
    if (path_semantic == PathSemantic::DATA_TEST) {
        return make_unique<Paths::DataTest::BFSEnum>(path_var, start, end, automaton, std::move(provider), std::move(helper));
    }
    else{
        return make_unique<Paths::DataTest::Naive::NaiveBFSEnum>(path_var, start, end, automaton, std::move(provider));
    }
}



std::unique_ptr<BindingIter> ConstraintPathPlan::get_unfixed(const SMTAutomaton& automaton, VarId start, VarId end) const {
    auto iter = start == end
                ? get_check(automaton, start, end)
                : get_enum(automaton, start, end);

    return std::make_unique<Paths::SMTUnfixedComposite>(
            path_var,
            start,
            end,
            automaton,
            get_provider(automaton),
            std::move(iter)
    );
}
bool ConstraintPathPlan::from_is_better_start_direction_smt() const {
    if (smt_automaton.get_total_states() == 1 || smt_automaton.decide_accept(0)) {
        return true;
    }

    double cost_normal_dir = 0;
    double cost_inverse_dir = 0;

    for (auto& transition : smt_automaton.from_to_connections[0]) {
        auto predicate_id = transition.type_id.id;
        auto it = quad_model.catalog.type2total_count.find(predicate_id);
        if (it != quad_model.catalog.type2total_count.end()) {
            cost_normal_dir += it->second;
        }
    }

    for (auto& transition : smt_inverted.from_to_connections[0]) {
        auto predicate_id = transition.type_id.id;
        auto it = quad_model.catalog.type2total_count.find(predicate_id);
        if (it != quad_model.catalog.type2total_count.end()) {
            cost_inverse_dir += it->second;
        }
    }

    if (cost_inverse_dir < cost_normal_dir) {
        return false;
    } else {
        return true;
    }
}

unique_ptr<BindingIter> ConstraintPathPlan::get_binding_iter() const {
    bool right_to_left = direction == Path::Direction::RIGHT_TO_LEFT;
    if (from_assigned) {
        if (to_assigned) {
            auto star_at_from = from_is_better_start_direction_smt();
            begin_at_left[path_var.id] = star_at_from != right_to_left;
            const SMTAutomaton &best_automaton = star_at_from ? smt_automaton : smt_inverted;
            Id start = star_at_from ? from : to;
            Id end = star_at_from ? to : from;
            return get_check(best_automaton, start, end);

        } else {
            begin_at_left[path_var.id] = !right_to_left;
            return get_enum(smt_automaton, from, to.get_var());
        }
    } else {
        if (to_assigned) {
            // enum starting on to
            begin_at_left[path_var.id] = right_to_left;
            return get_enum(smt_inverted, to, from.get_var());
        } else {
            auto star_at_from = from_is_better_start_direction_smt();
            begin_at_left[path_var.id] = star_at_from != right_to_left;
            const SMTAutomaton &best_automaton = star_at_from ? smt_automaton : smt_inverted;
            Id start = star_at_from ? from : to;
            Id end = star_at_from ? to : from;
            return get_unfixed(best_automaton, start.get_var(), end.get_var());
        }
    }
}
