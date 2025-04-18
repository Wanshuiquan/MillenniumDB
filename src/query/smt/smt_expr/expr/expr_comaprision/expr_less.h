#pragma once

#include <memory>

#include "query/smt/smt_expr/smt_expr.h"

namespace SMT {
class ExprLess : public Expr {
public:
    std::unique_ptr<Expr> lhs;
    std::unique_ptr<Expr> rhs;

    ExprLess(std::unique_ptr<Expr> lhs, std::unique_ptr<Expr> rhs) :
        lhs (std::move(lhs)),
        rhs (std::move(rhs)) { }
    ExprLess( const ExprLess& expr):
     lhs (std::unique_ptr<Expr>(expr.lhs.get())), rhs (std::unique_ptr<Expr>(expr.rhs.get()))
    {

    }
     std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprLess>(lhs->clone(), rhs->clone());
    }

    std::string to_smt_lib() const {
        auto add_epsilon = "  (+ epsilon   " + lhs -> to_smt_lib() + " ) ";
        return "( <= "  + add_epsilon +  rhs ->to_smt_lib() + " ) ";
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
