#pragma once

#include "query/smt/smt_expr/smt_expr.h"

namespace SMT {
class ExprUnaryMinus : public Expr {
public:
    std::unique_ptr<Expr> expr;

    ExprUnaryMinus(std::unique_ptr<Expr> expr) :
        expr (std::move(expr)) { }
    ExprUnaryMinus(const ExprUnaryMinus& expr) : expr (std::unique_ptr<SMT::Expr>(expr.expr.get())) { }
    std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprUnaryMinus>(expr->clone());
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }

    Sort get_sort() const override
    {
        return expr->get_sort();
    }
    std::string to_smt_lib()const{throw std::runtime_error("Not Support");}

    std::set<std::tuple<std::string, Sort, ObjectId>> get_all_attrs() const override {
        auto attrs =  expr->get_all_attrs();
        std::set<std::tuple<std::string, Sort, ObjectId>>  res = {};
        for (auto& attr : attrs) {
            auto name = std::get<0>(attr);
            auto id = std::get<2>(attr);
            res.insert(std::make_tuple(name, Sort::Num, id));
        }
        return res;
    }
    std::set<VarId> get_all_vars() const override {
        return expr->get_all_vars();
    }
 std::set<VarId> get_all_parameter() const override {
                return expr->get_all_parameter();

    }
    
};
} // namespace MQL
