//
// Created by heyang-li on 6/25/25.
//

#ifndef NAIVE_BFS_ENUM_H
#define NAIVE_BFS_ENUM_H



#pragma  once
#include <queue>
#include "query/executor/binding_iter.h"
#include "naive_search_state.h"
#include "query/parser/paths/automaton/smt_automaton.h"
#include "misc/arena.h"
#include "graph_models/quad_model/quad_model.h"
#include "query/executor/binding_iter/paths/data_test/query_data.h"
#include "boost/format.hpp"
namespace Paths::DataTest::Naive{


    class NaiveBFSEnum: public BindingIter {
        // Attributes determined in the constructor
        VarId         path_var;
        Id            start;
        VarId            end;
        const SMTAutomaton automaton;
        std::unique_ptr<IndexProvider> provider;

        // where the results will be written, determined in begin()
        Binding* parent_binding;

        // if `end` is an ObjectId, this has the same value
        // if `end` is a variable, this has its the value in the binding
        // its value is setted in begin() and reset()
        ObjectId end_object_id;
        // struct with all simple paths
        Arena<PathState> visited;

        // Queue for BFS
        std::queue<SearchState*> open;

        // Iterator for current node expansion
        std::unique_ptr<EdgeIter> iter;

        // The index of the transition being currently explored
        uint_fast32_t current_transition;

        // true in the first call of next() and after a reset()
        bool first_next = true;

        // Optimal distance to target node. UINT64_MAX means the node has not been explored yet.
        uint64_t optimal_distance = UINT64_MAX;
        // variables
        std::map<VarId, double_t> vars;
        // attributes
        std::set<std::tuple<std::string, ObjectId>> attributes;
        std::map<std::tuple<std::string, ObjectId>, double_t> real_attributes;
        std::map<std::tuple<std::string, ObjectId>, std::string> string_attributes;
        std::map<std::tuple<std::string, ObjectId>, bool> boolean_attributes;
        // odd progress is relate to an edge and even progress is relate to a node
        bool even= true;
        z3::solver s= get_smt_ctx().get_solver();

        bool check_sat (const z3::ast_vector_tpl<z3::expr>& formulas)
        {
            for (const auto& f: formulas) {
                get_smt_ctx().solver_add_condition(s,f);
            }
            get_smt_ctx().solver_add_epsilon_condition(s);

            switch (get_smt_ctx().check(s)) {
                case z3::unsat:s.reset(); return false;
                case z3::sat: {
                    auto model = get_smt_ctx().get_model(s);
                    for (const auto &ele:vars){
                        std::string name = get_query_ctx().get_var_name(ele.first);
                        z3::expr v = get_smt_ctx().get_var(name);
                        auto val = model.eval(v).as_double();
                        vars[ele.first] = val;
                    }
                    get_smt_ctx().solver_reset(s);
                    return true;
                }
                case z3::unknown:get_smt_ctx().solver_reset(s); return false;
                default: return false;
            }
        }
    public:
        // Statistics
        uint_fast32_t idx_searches = 0;
        uint_fast32_t exploration_depth = 0;
        ~NaiveBFSEnum() override
        {

            auto memory_consuption =  Z3_get_estimated_alloc_size()/ (1024* 1024);
            auto smt_operation_time = get_smt_ctx().get_other_run_time()/(1e6);
            auto smt_solver_time = get_smt_ctx().get_solver_run_time()/(1e6);

            std::cout << std::string(2, ' ') << "[begin: " << stat_begin << " next: " << stat_next
                      << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches << " solver_memory_consumption： " << memory_consuption << " MB "
                      << " z3_operation_time: " << smt_operation_time << " ms "
                      <<  "z3_solver_time: " << smt_solver_time << " ms "
                      << " exploration_depth： " << exploration_depth
                      << "]\n";
        }
        NaiveBFSEnum(
                VarId                          path_var,
                Id                             start,
                VarId                             end,
                SMTAutomaton                    automaton,
                std::unique_ptr<IndexProvider>  provider
        ) :
                path_var      (path_var),
                start         (start),
                end           (end),
                automaton     (automaton),
                provider      (std::move(provider)) {
            for (auto& ele: automaton.get_attributes()){
                attributes.emplace(ele);
            }
            for (auto& ele: automaton.get_parameters()){
                vars.emplace(ele, 0);
            }
        }

        // Explore neighbors searching for a solution.
        // returns a pointer to the object added to visited when a solution is found
        // or nullptr when there are no more results
        const SearchState* expand_neighbors(SearchState& );

        void print(std::ostream& os, int indent, bool stats) const override;

        void _begin(Binding& parent_binding) override;

        void _reset() override;

        bool _next() override;
        void update_value(uint64_t);
        void substitution(uint64_t, z3::ast_vector_tpl<z3::expr>&, std::string);
        void assign_nulls() override {
            parent_binding->add(path_var, ObjectId::get_null());
        }







        // Set iterator for current node + transition
        inline void set_iter(const SearchState& s) {
            // Get iterator from custom index
            auto& transition = automaton.from_to_connections[s.automaton_state][current_transition];
            auto id = QuadObjectId::get_named_node(transition.type);
            iter = provider->get_iter(id.id, transition.inverse, s.path_state->node_id.id);
            idx_searches++;
        }


    };
}





#endif //NAIVE_BFS_ENUM_H
