#pragma once

#include "query/smt/smt_expr/smt_expr.h"

namespace SMT {
class ExprSubtraction : public Expr {
public:
    std::unique_ptr<Expr> lhs;
    std::unique_ptr<Expr> rhs;

    ExprSubtraction(std::unique_ptr<Expr> lhs, std::unique_ptr<Expr> rhs) :
        lhs (std::move(lhs)),
        rhs (std::move(rhs)) { }
    ExprSubtraction( const ExprSubtraction& expr):
     lhs (expr.lhs.get()), rhs (expr.rhs.get())
    {

    }

    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprSubtraction>(lhs->clone(), rhs->clone());
    }
    std::string to_smt_lib()const{
        return "( - "  + lhs -> to_smt_lib() + "  "+ rhs -> to_smt_lib() + " ) ";
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }

    Sort get_sort() const override
    {
        return compare(lhs -> get_sort(), rhs -> get_sort());
    }

    std::set<VarId> get_all_vars() const override {
        std::set<VarId> res = lhs->get_all_vars();
        auto rhs_vars = rhs->get_all_vars();
        res.insert(rhs_vars.begin(), rhs_vars.end());
        return res;
    }

    std::set<std::tuple<std::string, Sort, ObjectId>> get_all_attrs() const override {
        std::set<std::tuple<std::string, Sort, ObjectId>> res = lhs->get_all_attrs();
        auto rhs_vars = rhs->get_all_attrs();
        res.insert(rhs_vars.begin(), rhs_vars.end());
        std::set<std::tuple<std::string, Sort, ObjectId>>  r = {};
        for (auto& attr : res) {
            auto name = std::get<0>(attr);
            auto id = std::get<2>(attr);
            r.insert(std::make_tuple(name, Sort::Num, id));
        }
        return r;
    }

    std::set<VarId> get_all_parameter() const override {
        std::set<VarId> res = lhs->get_all_parameter();
        auto rhs_vars = rhs->get_all_parameter();
        res.insert(rhs_vars.begin(), rhs_vars.end());
        return res;
    }
};
} // namespace MQL
