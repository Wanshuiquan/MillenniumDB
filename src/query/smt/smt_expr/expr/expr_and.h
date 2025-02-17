#pragma once

#include <memory>
#include <vector>

#include "query/smt/smt_expr/smt_expr.h"
#include "boost/algorithm/string/join.hpp"

namespace SMT {
class ExprAnd : public Expr {
public:
    std::vector<std::unique_ptr<Expr>> and_list;

    explicit ExprAnd(std::vector<std::unique_ptr<Expr>>&& and_list) :
        and_list (std::move(and_list)) { }
    explicit ExprAnd(const ExprAnd& and_expr) : and_list (std::vector<std::unique_ptr<Expr>>())
    {
        for (auto& expr : and_expr.and_list)
        {
            and_list.push_back (expr->clone());
        }
    }
    std::string to_smt_lib()const{    
        if (and_list.size() > 1){
            std::vector<std::string> vec;
            for (auto& f: and_list){
                vec.push_back(f->to_smt_lib());
            }
            auto formulas = boost::algorithm::join(vec, "");
            return "(assert ( and" + formulas + "))";
        }
        else{
            return "( assert " + and_list[0] ->to_smt_lib() + " )";
        }

}
    [[nodiscard]] std::unique_ptr<Expr> clone() const override {
        std::vector<std::unique_ptr<Expr>> and_list_clone;
        and_list_clone.reserve(and_list.size());
        for (auto& child_expr : and_list) {
            and_list_clone.push_back(child_expr->clone());
        }
        return std::make_unique<ExprAnd>(std::move(and_list_clone));
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }

    [[nodiscard]] bool has_aggregation() const override {
        for (auto& expr : and_list) {
            if (expr->has_aggregation())
                return true;
        }
        return false;
    }

    std::set<VarId> get_all_vars() const override {
        std::set<VarId> res;
        for (auto& expr: and_list) {
            for (auto& var : expr->get_all_vars()) {
                res.insert(var);
            }
        }
        return res;
    }

    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override {
        std::set<std::tuple<std::string, ObjectId>> res;
        for (auto& expr: and_list) {
            for (auto& var : expr->get_all_attrs()) {
                res.insert(var);
            }
        }
        return res;
    }

    
    std::set<VarId> get_all_parameter() const override {
        std::set<VarId> res;
        for (auto& expr: and_list) {
            for (auto& var : expr->get_all_parameter()) {
                res.insert(var);
            }
        }
        return res;
    }
};
} // namespace MQL
