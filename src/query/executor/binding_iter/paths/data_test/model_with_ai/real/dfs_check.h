#pragma once

#include <map>
#include <memory>
#include <stack>
#include <set>

#include "boost/format.hpp"

#include "misc/arena.h"
#include "misc/logger.h"

#include "query/executor/binding_iter.h"
#include "query/executor/binding_iter/paths/data_test/preprocess_dfs_check.h"
#include "query/executor/binding_iter/paths/data_test/model/macro_state_antichain.h"
#include "query/executor/binding_iter/paths/data_test/query_data.h"
#include "query/executor/binding_iter/paths/data_test/search_state.h"
#include "real_search_state.h"
#include "query/parser/paths/automaton/smt_automaton.h"
#include "query/smt/real/ai_entailment_pipeline.h"

namespace Paths::DataTest::Real {

using Paths::DataTest::PathState;

class DFSCheck : public BindingIter {
    VarId path_var;
    Id start;
    Id end;
    const SMTAutomaton automaton;
    std::unique_ptr<IndexProvider> provider;
    std::unique_ptr<DFSPreCheck> preprocessor;

    Binding* parent_binding;
    ObjectId end_object_id;

    Arena<PathState> visited;
    Paths::DataTest::MacroStateAntichain<MacroStateReal> visited_product_graph;
    std::stack<MacroStateReal> open;

    std::unique_ptr<EdgeIter> iter;
    uint_fast32_t current_transition;
    bool first_next = true;

    std::map<VarId, double> vars;

    std::set<std::tuple<std::string, ObjectId>> attributes;
    std::map<std::tuple<std::string, ObjectId>, double> real_attributes;
    std::map<std::tuple<std::string, ObjectId>, std::string> string_attributes;
    std::map<std::tuple<std::string, ObjectId>, bool> boolean_attributes;

    z3::solver solver = get_smt_ctx().get_solver();
    SMT::Real::AIEntailmentPipeline entailment_pipeline;

public:
    uint_fast32_t idx_searches = 0;
    uint_fast32_t exploration_depth = 0;

    ~DFSCheck() override {
        const double memory_consumption = static_cast<double>(Z3_get_estimated_alloc_size()) / (1024.0 * 1024.0);
        const double smt_operation_time = static_cast<double>(get_smt_ctx().get_other_run_time()) / (1000.0 * 1000.0);
        const double smt_solver_time = static_cast<double>(get_smt_ctx().get_solver_run_time()) / (1000.0 * 1000.0);

        logger.info() << std::string(2, ' ') << "\n[begin: " << stat_begin << " next: " << stat_next
                      << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches
                      << " solver_memory_consumption: " << memory_consumption << " MB "
                      << " z3_operation_time: " << smt_operation_time << " ms "
                      << " z3_solver_time: " << smt_solver_time << " ms "
                      << get_smt_ctx().pipeline_timers_to_string()
                      << " exploration_depth: " << exploration_depth
                      << "]\n";
    }

    DFSCheck(
            VarId path_var,
            const Id& start,
            const Id& end,
            SMTAutomaton automaton,
            std::unique_ptr<IndexProvider> provider,
            std::unique_ptr<DFSPreCheck> preprocessor
    ) :
            path_var(path_var),
            start(start),
            end(end),
            automaton(automaton),
            provider(std::move(provider)),
            preprocessor(std::move(preprocessor))
    {
        for (auto& attr : automaton.get_attributes()) {
            attributes.emplace(attr);
        }
        for (auto& param : automaton.get_parameters()) {
            vars.emplace(param, 0);
        }
    }

    const PathState* expand_neighbors(MacroStateReal& macro_state);
    void print(std::ostream& os, int indent, bool stats) const override;
    void _begin(Binding& parent_binding) override;
    void _reset() override;
    bool _next() override;

    bool eval_check(uint64_t obj, MacroStateReal& macro_state, const std::string& formula);
    SMT::CheckStatus check_constraints(const MacroStateReal& macro_state);
    void set_model(z3::solver& sat_solver);
    void update_value(uint64_t obj);

    void assign_nulls() override {
        parent_binding->add(path_var, ObjectId::get_null());
    }

    inline void set_iter(const MacroStateReal& macro_state) {
        auto& transition = automaton.from_to_connections[macro_state.automaton_state][macro_state.dfs_transition];
        macro_state.dfs_iter = provider->get_iter(transition.type_id.id, transition.inverse, macro_state.path_state->node_id.id);
        idx_searches++;
    }
};

} // namespace Paths::DataTest::Real
