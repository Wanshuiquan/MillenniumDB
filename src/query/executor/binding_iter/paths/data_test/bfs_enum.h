//
// Created by lhy on 9/16/24.
//

#ifndef MILLENNIUMDB_BFS_ENUM_H
#define MILLENNIUMDB_BFS_ENUM_H
#pragma  once

#include "query/smt/smt_ctx.h"
#include <queue>
#include <set>
#include "query/executor/binding_iter.h"
#include "search_state.h"
#include "query/parser/paths/automaton/smt_automaton.h"
#include "preprocess_enum.h"
#include "misc/arena.h"
#include "graph_models/quad_model/quad_model.h"
#include "query_data.h"
#include "boost/format.hpp"
#include "unordered_map"
namespace Paths::DataTest{
    class BFSEnum: public BindingIter{
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
        std::set<MacroState> visited_product_graph;
        // Queue for BFS
        std::queue<MacroState> open;

        // Iterator for current node expansion
        std::unique_ptr<EdgeIter> iter;

        // preprocessing
        std::unique_ptr<PreEnum> preprocessor;

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
        z3::solver solver = get_smt_ctx().get_solver();

        // Cache for preloading neighbors
        std::unordered_map<uint64_t, std::vector<std::pair<uint64_t, uint64_t>>> neighbor_cache;

    public:
        // Statistics
        uint_fast32_t idx_searches = 0;
        uint_fast32_t exploration_depth = 0;
        ~BFSEnum() override
        {
            std::cout<< "preprocessor: ";
            preprocessor ->print(std::cout, 2, true);

            auto memory_consuption =  Z3_get_estimated_alloc_size()/ (1024.0* 1024.0);
            auto smt_operation_time = get_smt_ctx().get_other_run_time()/(1000.0 * 1000.0);
            auto smt_solver_time = get_smt_ctx().get_solver_run_time()/(1000.0 * 1000.0);

            std::cout << std::string(2, ' ') << "\n[begin: " << stat_begin << " next: " << stat_next
                      << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches << " solver_memory_consumption: " << memory_consuption << " MB "
                      << " z3_operation_time: " << smt_operation_time << " ms "
                      <<  "z3_solver_time: " << smt_solver_time << " ms "
                      << " exploration_depth: " << exploration_depth
                      << "]\n";
        }
        BFSEnum(    VarId        path_var,
                    const  Id&             start,
                    VarId              end,
                    SMTAutomaton        automaton,
                    std::unique_ptr<IndexProvider>  provider,
                    std::unique_ptr<PreEnum> preprocessor
        ) :
                path_var      (path_var),
                start         (start),
                end           (end),
                automaton     (automaton),
                provider      (std::move(provider)),
                preprocessor (std::move(preprocessor)){
            for (auto& ele: automaton.get_attributes()){
                attributes.emplace(ele);
            }
            for (auto& ele: automaton.get_parameters()){
                vars.emplace(ele, 0);
            }
        }

        void print(std::ostream& os, int indent, bool stats) const override;
        // Explore neighbors searching for a solution.
        // returns a pointer to the object added to visited when a solution is found
        // or nullptr when there are no more results
        const PathState* expand_neighbors(MacroState&);


        void _begin(Binding& parent_binding) override;

        void _reset() override;

        bool _next() override;
        bool eval_check(uint64_t obj, MacroState&, const std::string& );
        void update_value(uint64_t);

        void assign_nulls() override {
            parent_binding->add(end, ObjectId::get_null());
            parent_binding->add(path_var, ObjectId::get_null());
        }

        // Set iterator for current node + transition
        inline void set_iter(const MacroState& s) {
            // Get iterator from custom index
            auto& transition = automaton.from_to_connections[s.automaton_state][current_transition];
            auto id = QuadObjectId::get_named_node(transition.type);
            iter = provider->get_iter(id.id, transition.inverse, s.path_state->node_id.id);
            idx_searches++;
        }

        // Preload all neighbors of a node
        const std::vector<std::pair<uint64_t, uint64_t>>& preload_neighbors(uint64_t node_id) {
            auto it = neighbor_cache.find(node_id);
            if (it != neighbor_cache.end()) {
                return it->second;
            }

            std::vector<std::pair<uint64_t, uint64_t>> neighbors;
            for (const auto& edge : automaton.from_to_connections[node_id]) {
                uint64_t target_id = edge.to;
                uint64_t label_id = QuadObjectId::get_string(edge.type).id;
                neighbors.emplace_back(target_id, label_id);
            }

            neighbor_cache[node_id] = neighbors;
            return neighbor_cache[node_id];
        }
    };
}



#endif //MILLENNIUMDB_BFS_ENUM_H
