#pragma once

#include "query/query_context.h"
#include "query/smt/smt_expr/smt_expr.h"

namespace SMT {
class ExprVarProperty : public Expr {
public:
    VarId var_without_property; // ?x

    ObjectId key;

    VarId var_with_property; // ?x.key

    ExprVarProperty(VarId var_without_property, ObjectId key, VarId var_with_property) :
        var_without_property (var_without_property),
        key                  (key),
        var_with_property    (var_with_property) { }
    ExprVarProperty(ExprVarProperty& exp) : var_without_property(exp.var_without_property), key(exp.key), var_with_property(exp.var_with_property) { }
    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprVarProperty>(
            var_without_property,
            key,
            var_with_property
        );
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }
//
    std::string to_smt_lib()const{throw std::runtime_error("Not Support");}
    bool has_aggregation() const override { return false; }

    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override{
        return { };
    }
    std::set<VarId> get_all_vars() const override {
        return { var_with_property };
    }

    std::set<VarId> get_all_parameter() const override{
        return {var_with_property}; 
    }
};
} // namespace MQL
