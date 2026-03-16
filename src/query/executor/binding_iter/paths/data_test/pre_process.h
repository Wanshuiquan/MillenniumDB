//
// Created by lhy on 9/16/24.
//
#pragma once

#include "query/smt/smt_ctx.h"

#include <stack>
#include "query/executor/binding_iter.h"
#include "search_state.h"
#include "query/parser/paths/automaton/smt_automaton.h"
namespace Paths::DataTest{
    class PreEnum: public BindingIter{
        // Attributes determined in the constructor
        Id            start;
        const SMTAutomaton automaton;
        std::unique_ptr<IndexProvider> provider;

        // where the results will be written, determined in begin()
        Binding* parent_binding;
        ObjectId current_start;
        bool first_next = true;

        // if `end` is an ObjectId, this has the same value
        // if `end` is a variable, this has its the value in the binding
        // its value is setted in begin() and reset()
        ObjectId end_object_id;
        // struct with all simple paths
        // Queue for BFS
        std::stack<PreSearchState> open;
        std::set<uint64_t> current_state_nodes;
        // Iterator for current node expansion
        std::unique_ptr<EdgeIter> iter;

        // The index of the transition being currently explored
        uint_fast32_t current_transition;

        // true in the first call of next() and after a reset()


        // Optimal distance to target node. UINT64_MAX means the node has not been explored yet.
        static VarId path_var ;

    public:
        // Statistics
        uint_fast32_t idx_searches = 0;
        uint_fast32_t exploration_depth = 0;
        ~PreEnum() = default;
        PreEnum(   const  Id&  start,
                    SMTAutomaton   automaton,
                    std::unique_ptr<IndexProvider>  provider
        ) :
            start(start),
            automaton(automaton),
            provider(std::move(provider))
        {
            SMTCtx::log_comment("start exploration");
        }

        void print(std::ostream& os, int indent, bool stats) const override;
        // Explore neighbors searching for a solution.
        // returns a pointer to the object added to visited when a solution is found
        // or nullptr when there are no more results
        const PathState* expand_neighbors(PreSearchState&);

        void assign_nulls() override
        {

        }
        void _begin(Binding& parent_binding) override;

        void _reset() override;

        bool _next() override;




        // Set iterator for current node + transition
         void set_iter(const PreSearchState& s) {
            // Get iterator from custom index
            auto& transition = automaton.from_to_connections[s.automaton_state][current_transition];
            auto id = QuadObjectId::get_named_node(transition.type);
            iter = provider->get_iter(id.id, transition.inverse, s.path_state->node_id.id);
            idx_searches++;
        }

    };
}



