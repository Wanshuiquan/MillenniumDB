#pragma once

#include "query/query_context.h"
#include "query/smt/smt_expr/smt_expr.h"


namespace SMT {
class ExprVar : public Expr {
public:
    VarId var;

    ExprVar(VarId var) :
        var (var) { }
    ExprVar(ExprVar& expr) :var(expr.var) { }
    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprVar>(var);
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }
    std::string to_smt_lib() const {return get_query_ctx().get_var_name(var);};
    bool has_aggregation() const override { return false; }

    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override{
        return { };
    }
    std::set<VarId> get_all_vars() const override {
        return { var };
    }

    std::set<VarId> get_all_parameter() const override{
        return {var}; 
    }
};
} // namespace MQL
