#pragma once

#include <memory>

#include "query/smt/smt_expr/smt_expr.h"
namespace SMT {
class ExprEquals : public Expr {
public:
    std::unique_ptr<Expr> lhs;
    std::unique_ptr<Expr> rhs;

    ExprEquals(std::unique_ptr<Expr> lhs, std::unique_ptr<Expr> rhs) :
        lhs (std::move(lhs)),
        rhs (std::move(rhs)) { }
    ExprEquals( const ExprEquals& expr):
    lhs (expr.lhs.get()), rhs (expr.rhs.get())
    {

    }
    std::string to_smt_lib() const{
        return "( = "  + lhs -> to_smt_lib() + "  " + rhs -> to_smt_lib() + " ) ";

    }
    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprEquals>(lhs->clone(), rhs->clone());
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
        for (auto& var : rhs->get_all_vars()) {
            res.insert(var);
        }
        return res;
    }

    std::set<std::tuple<std::string, Sort, ObjectId>> get_all_attrs() const override {
        auto lhs_sort = lhs->get_sort();
        auto rhs_sort = rhs->get_sort();
        auto max = infer(lhs_sort, rhs_sort);
        assert(max != Sort::Bot);
        if (max == Sort::Num) {
            std::set<std::tuple<std::string, Sort, ObjectId>>  res = {};
            auto lhs_attr = lhs -> get_all_attrs();
            auto rhs_attr = rhs -> get_all_attrs();
            for (auto& attr : lhs_attr) {
                auto name = std::get<0>(attr);
                auto id = std::get<2>(attr);
                res.insert(std::make_tuple(name, Sort::Num, id));
            }
            for (auto& attr : rhs_attr) {
                auto name = std::get<0>(attr);
                auto id = std::get<2>(attr);
                res.insert(std::make_tuple(name, Sort::Num, id));
            }
            return  res;
        }

        if (max == Sort::String) {
            std::set<std::tuple<std::string, Sort, ObjectId>>  res = {};
            auto lhs_attr = lhs -> get_all_attrs();
            auto rhs_attr = rhs -> get_all_attrs();
            for (auto& attr : lhs_attr) {
                auto name = std::get<0>(attr);
                auto id = std::get<2>(attr);
                res.insert(std::make_tuple(name, Sort::String, id));
            }
            for (auto& attr : rhs_attr) {
                auto name = std::get<0>(attr);
                auto id = std::get<2>(attr);
                res.insert(std::make_tuple(name, Sort::String, id));
            }
            return  res;
        }
        throw std::runtime_error("not implemented");
    }

        std::set<VarId> get_all_parameter() const override {
        std::set<VarId> res = lhs->get_all_parameter();
        auto rhs_vars = rhs->get_all_parameter();
        res.insert(rhs_vars.begin(), rhs_vars.end());
        return res;
    }
};
} // namespace MQL
