#pragma once

#include <map>
#include <memory>
#include <queue>
#include <set>

#include "boost/format.hpp"

#include "misc/arena.h"
#include "misc/logger.h"

#include "query/executor/binding_iter.h"
#include "query/executor/binding_iter/paths/data_test/preprocess_enum.h"
#include "query/executor/binding_iter/paths/data_test/query_data.h"
#include "query/executor/binding_iter/paths/data_test/search_state.h"
#include "query/executor/binding_iter/paths/data_test/integer/interger_search_state.h"
#include "query/parser/paths/automaton/smt_automaton.h"
#include "query/smt/int/abstract_rewriter.h"
#include "query/smt/int/entailment_pipeline.h"

namespace Paths::DataTest::Integer {

using Paths::DataTest::PathState;
using Paths::DataTest::is_simple_path;

template<bool END_CHECK>
class BFSEnum : public BindingIter {
    VarId path_var;
    Id start;
    VarId end;
    const SMTAutomaton automaton;
    std::unique_ptr<IndexProvider> provider;
    std::unique_ptr<PreEnum> preprocessor;

    Binding* parent_binding;
    ObjectId end_object_id;

    Arena<PathState> visited;
    std::set<MacroStateInt> visited_product_graph;
    std::queue<MacroStateInt> open;

    std::unique_ptr<EdgeIter> iter;
    uint_fast32_t current_transition;
    bool first_next = true;

    std::map<VarId, int64_t> vars;

    std::set<std::tuple<std::string, ObjectId>> attributes;
    std::map<std::tuple<std::string, ObjectId>, int64_t> int_attributes;
    std::map<std::tuple<std::string, ObjectId>, std::string> string_attributes;
    std::map<std::tuple<std::string, ObjectId>, bool> boolean_attributes;

    z3::solver solver = get_smt_ctx().get_solver();
    SMT::Int::EntailmentPipeline64 entailment_pipeline;

public:
    uint_fast32_t idx_searches = 0;
    uint_fast32_t exploration_depth = 0;

    ~BFSEnum() override {
        const double memory_consumption = static_cast<double>(Z3_get_estimated_alloc_size()) / (1024.0 * 1024.0);
        const double smt_operation_time = static_cast<double>(get_smt_ctx().get_other_run_time()) / (1000.0 * 1000.0);
        const double smt_solver_time = static_cast<double>(get_smt_ctx().get_solver_run_time()) / (1000.0 * 1000.0);

        logger.info() << std::string(2, ' ') << "\n[begin: " << stat_begin << " next: " << stat_next
                      << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches
                      << " solver_memory_consumption: " << memory_consumption << " MB "
                      << " z3_operation_time: " << smt_operation_time << " ms "
                      << " z3_solver_time: " << smt_solver_time << " ms "
                      << " exploration_depth: " << exploration_depth
                      << "]\n";
    }

    BFSEnum(
            VarId path_var,
            const Id& start,
            VarId end,
            SMTAutomaton automaton,
            std::unique_ptr<IndexProvider> provider,
            std::unique_ptr<PreEnum> preprocessor
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

    const PathState* expand_neighbors(MacroStateInt& macro_state);
    void print(std::ostream& os, int indent, bool stats) const override;
    void _begin(Binding& parent_binding) override;
    void _reset() override;
    bool _next() override;

    bool eval_check(uint64_t obj, MacroStateInt& macro_state, const std::string& formula);
    bool check_constraints(const MacroStateInt& macro_state);
    void set_model(z3::solver& sat_solver);
    void update_value(uint64_t obj);

    void assign_nulls() override {
        parent_binding->add(end, ObjectId::get_null());
        parent_binding->add(path_var, ObjectId::get_null());
    }

    inline void set_iter(const MacroStateInt& state) {
        auto& transition = automaton.from_to_connections[state.automaton_state][current_transition];
        auto id = QuadObjectId::get_named_node(transition.type);
        iter = provider->get_iter(id.id, transition.inverse, state.path_state->node_id.id);
        idx_searches++;
    }
};

} // namespace Paths::DataTest::Integer
