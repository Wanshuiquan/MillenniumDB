#pragma once

#include "query/executor/binding_iter/paths/index_provider/path_index.h"
#include "query/optimizer/plan/plan.h"
#include "query/parser/op/mql/graph_pattern/op_path.h"
#include "query/parser/paths/regular_path_expr.h"
#include "query/query_context.h"

namespace MQL {
class PathPlan : public Plan {
public:
    PathPlan(
        std::vector<bool>& begin_at_left,
        OpPath::Direction direction,
        VarId path_var,
        Id from,
        Id to,
        RegularPathExpr& path,
        PathSemantic semantic,
        uint64_t K
    );

    PathPlan(const PathPlan& other) :
        begin_at_left (other.begin_at_left),
        direction     (other.direction),
        path_var      (other.path_var),
        from          (other.from),
        to            (other.to),
        path          (other.path),
        from_assigned (other.from_assigned),
        to_assigned   (other.to_assigned),
        path_semantic (other.path_semantic),
        automaton          (other.automaton),
        automaton_inverted (other.automaton_inverted),
        smt_automaton (other.smt_automaton),
        smt_inverted(other.smt_inverted)
        { }

    std::unique_ptr<Plan> clone() const override
    {
        return std::make_unique<PathPlan>(*this);
    }

    int relation_size() const override
    {
        return 3;
    }

    double estimate_cost() const override;
    double estimate_output_size() const override;

    std::set<VarId> get_vars() const override;
    void set_input_vars(const std::set<VarId>& input_vars) override;

    std::unique_ptr<BindingIter> get_binding_iter() const override;

    bool get_leapfrog_iter(std::vector<std::unique_ptr<LeapfrogIter>>&, std::vector<VarId>&, uint_fast32_t&)
        const override
    {
        return false;
    }

    void print(std::ostream& os, int indent) const override;

private:
    std::vector<bool>& begin_at_left;
    OpPath::Direction direction;
    const VarId path_var;
    const Id from;
    const Id to;
    RegularPathExpr& path;
    uint64_t K;

    bool from_assigned;
    bool to_assigned;

    PathSemantic path_semantic;

    RPQ_DFA automaton;
    RPQ_DFA automaton_inverted;

    SMTAutomaton smt_automaton;
    SMTAutomaton smt_inverted;
    bool from_is_better_start_direction() const;

    // Construct index provider for this automaton
    std::unique_ptr<Paths::IndexProvider> get_provider(const RPQ_DFA& automaton) const;

    std::unique_ptr<BindingIter> get_check(const RPQ_DFA& automaton, Id start, Id end) const;
    std::unique_ptr<BindingIter> get_enum(const RPQ_DFA& automaton, Id start, VarId end) const;
    std::unique_ptr<BindingIter> get_unfixed(const RPQ_DFA& automaton, VarId start, VarId end) const;

    //Construct index provider for SMT Automaton

    std::unique_ptr<Paths::IndexProvider> get_provider(const SMTAutomaton& automaton) const;
    std::unique_ptr<BindingIter> get_check(const SMTAutomaton& automaton, Id start, Id end) const;
    std::unique_ptr<BindingIter> get_enum(const SMTAutomaton& automaton, Id start, VarId end) const;
    std::unique_ptr<BindingIter> get_unfixed(const SMTAutomaton& automaton, VarId start, VarId end) const;

    bool from_is_better_start_direction_smt() const;
};
} // namespace MQL
