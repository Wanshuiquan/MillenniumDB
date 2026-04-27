#pragma once

#include "graph_models/object_id.h"
#include "query/query_context.h"
#include "query/smt/smt_expr/smt_expr.h"
#include "query/executor/query_executor/mql/return_executor.h"
#include "query/smt/lra/lra_smt_operations.h"

namespace SMT {
class ExprConstant : public Expr {
public:
    ObjectId value;

    ExprConstant(ObjectId value) :
        value (value) { }
    ExprConstant(const ExprConstant &e) :value(e.value){}
    
    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprConstant>(value);
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }



    bool has_aggregation() const override { return false; }

    std::set<VarId> get_all_vars() const override {
        return { };
    }
    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override {
       return {};
    }
    std::set<VarId> get_all_parameter() const override {
        return {};
    }
};
} // namespace MQL
