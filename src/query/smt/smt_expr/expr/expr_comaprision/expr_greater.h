#pragma once

#include <memory>

#include "query/smt/smt_expr/smt_expr.h"

namespace SMT {
class ExprGreater : public Expr {
public:
    std::unique_ptr<Expr> lhs;
    std::unique_ptr<Expr> rhs;

    ExprGreater(std::unique_ptr<Expr> lhs, std::unique_ptr<Expr> rhs) :
        lhs (std::move(lhs)),
        rhs (std::move(rhs)) { }
    ExprGreater( const ExprGreater& expr):
     lhs (expr.lhs.get()), rhs (expr.rhs.get())
    {

    }
     std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprGreater>(lhs->clone(), rhs->clone());
    }

    std::string to_smt_lib() const {
        auto add_epsilon = "  (+ epsilon   " + rhs -> to_smt_lib() + " ) ";
        return "( >=  "  + lhs -> to_smt_lib() +  add_epsilon + " )";

    }
    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }

    bool has_aggregation() const override {
        return lhs->has_aggregation() || rhs->has_aggregation();
    }

    std::set<VarId> get_all_vars() const override {
        std::set<VarId> res = lhs->get_all_vars();
        for (auto& var : rhs->get_all_vars()) {
            res.insert(var);
        }
        return res;
    }

    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override {
        std::set<std::tuple<std::string, ObjectId>> res = lhs->get_all_attrs();
        auto rhs_vars = rhs->get_all_attrs();
        res.insert(rhs_vars.begin(), rhs_vars.end());
        return res;
    }

    std::set<VarId> get_all_parameter() const override {
        std::set<VarId> res = lhs->get_all_parameter();
        auto rhs_vars = rhs->get_all_parameter();
        res.insert(rhs_vars.begin(), rhs_vars.end());
        return res;
    }
};
} // namespace MQL
