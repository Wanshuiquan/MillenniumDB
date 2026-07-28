#pragma once

#include <string>
#include <utility>

#include "query/query_context.h"
#include "query/smt/smt_expr/smt_expr.h"

namespace SMT {
class ExprVarRegister : public Expr {
public:
    std::string name;

    explicit ExprVarRegister(std::string name) : name(std::move(name)) { }
    ExprVarRegister(const ExprVarRegister& exp) : name(exp.name) { }
    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprVarRegister>(name);
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }
    bool has_aggregation() const override { return false; }

    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override{
        return { };
    }
    std::set<VarId> get_all_vars() const override {
        return { };
    }

    std::set<VarId> get_all_parameter() const override{
        return { };
    }

};
} // namespace SMT
