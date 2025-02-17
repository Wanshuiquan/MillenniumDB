//
// Created by lhy on 9/16/24.
//

#ifndef MILLENNIUMDB_BFS_ENUM_H
#define MILLENNIUMDB_BFS_ENUM_H
#pragma  once
#include <queue>
#include "query/executor/binding_iter.h"
#include "search_state.h"
#include "query/parser/paths/automaton/smt_automaton.h"
#include "misc/arena.h"
#include "storage/index/record.h"
#include "graph_models/quad_model/quad_model.h"
#include "query_data.h"

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
        robin_hood::unordered_set<MacroState> visited_product_graph;

        // Queue for BFS
        std::queue<MacroState *> open;

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
        // odd progress is relate to an edge and even progress is relate to a node
        bool even= true;
        z3::solver solver = z3::solver(get_smt_ctx().context);

    public:
        // Statistics
        uint_fast32_t idx_searches = 0;

        BFSEnum(    VarId        path_var,
                    const  Id&             start,
                    VarId              end,
                    SMTAutomaton        automaton,
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

        void accept_visitor(BindingIterVisitor& visitor) override;
        // Explore neighbors searching for a solution.
        // returns a pointer to the object added to visited when a solution is found
        // or nullptr when there are no more results
        const PathState* expand_neighbors(MacroState&);


        void _begin(Binding& parent_binding) override;

        void _reset() override;

        bool _next() override;
        bool eval_check(uint64_t obj, MacroState&, std::string );
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

    };
}



#endif //MILLENNIUMDB_BFS_ENUM_H
