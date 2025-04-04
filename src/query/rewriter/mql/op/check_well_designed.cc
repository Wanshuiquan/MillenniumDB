#include "check_well_designed.h"

#include "query/parser/op/mql/ops.h"

using namespace MQL;

void CheckWellDesigned::visit(OpOptional& op_optional) {
    auto local_vars = op_optional.op->get_all_vars();

    for (const auto& var : local_vars) {
        if (global_vars.find(var) != global_vars.end() && parent_vars.find(var) == parent_vars.end()) {
            throw QuerySemanticException("Query is not well defined. Var " + std::to_string(var.id) + " is breaking the rule");
        }
        global_vars.insert(var);
    }

    parent_vars = local_vars;
    for (auto& optional_child : op_optional.optionals) {
        optional_child->accept_visitor(*this);
        parent_vars = local_vars;
    }
}


void CheckWellDesigned::visit(OpBasicGraphPattern& op_basic_graph_pattern) {
    auto local_vars = op_basic_graph_pattern.get_all_vars();

    for (const auto& var : local_vars) {
        if (global_vars.find(var) != global_vars.end() && parent_vars.find(var) == parent_vars.end()) {
            throw QuerySemanticException("Query is not well defined. Var "
                + get_query_ctx().get_var_name(var)
                + " is breaking the rule");
        }
        global_vars.insert(var);
    }
}


void CheckWellDesigned::visit(OpSet& op_set) {
    op_set.op->accept_visitor(*this);
}


void CheckWellDesigned::visit(OpReturn& op_return) {
    op_return.op->accept_visitor(*this);
}


void CheckWellDesigned::visit(OpWhere& op_where) {
    op_where.op->accept_visitor(*this);
}


void CheckWellDesigned::visit(OpGroupBy& op_group_by) {
    op_group_by.op->accept_visitor(*this);
}


void CheckWellDesigned::visit(OpOrderBy& op_order_by) {
    op_order_by.op->accept_visitor(*this);
}

