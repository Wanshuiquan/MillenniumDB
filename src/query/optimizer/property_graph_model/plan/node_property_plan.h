#pragma once

#include "query/query_context.h"
#include "query/optimizer/plan/plan.h"

class NodePropertyPlan : public Plan {
public:
    NodePropertyPlan(Id object, Id key, Id value);

    NodePropertyPlan(const NodePropertyPlan& other) :
        object          (other.object),
        key             (other.key),
        value           (other.value),
        object_assigned (other.object_assigned),
        key_assigned    (other.key_assigned),
        value_assigned  (other.value_assigned) { }

    std::unique_ptr<Plan> clone() const override {
        return std::make_unique<NodePropertyPlan>(*this);
    }

    int relation_size() const override { return 3; }

    double estimate_cost() const override;
    double estimate_output_size() const override;

    std::set<VarId> get_vars() const override;
    void set_input_vars(const std::set<VarId>& input_vars) override;

    std::unique_ptr<BindingIter> get_binding_iter() const override;

    bool get_leapfrog_iter(std::vector<std::unique_ptr<LeapfrogIter>>& leapfrog_iters,
                           std::vector<VarId>&                         var_order,
                           uint_fast32_t&                              enumeration_level) const override;

    void print(std::ostream& os, int indent) const override;

private:
    Id object;
    Id key;
    Id value;

    bool object_assigned;
    bool key_assigned;
    bool value_assigned;
};
