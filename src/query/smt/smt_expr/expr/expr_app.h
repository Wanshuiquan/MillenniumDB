//
// Created by heyang-li on 4/22/25.
//
#pragma once

#ifndef EXPR_APP_H
#define EXPR_APP_H
#include <memory>
#include <vector>

#include "query/smt/smt_expr/smt_expr.h"
#include "boost/algorithm/string/join.hpp"
enum Operator {
    And,
    Add,
    Mul,
    Sub,
    UniMin,
    Lte,
    Gte,
    Lt,
    Gt,
    Eq,
    Neq,
};

inline std::string op_str(Operator op)
{
    switch (op) {
        case And: return "and";
        case Add: return "+";
        case Mul: return "*";
        case Sub: return "-";
        case UniMin: return "-";
        case Lt: return "<";
        case Gt: return ">";
        case Gte: return ">=";
        case Lte: return "<=";
        case Eq: return "=";
        case Neq: return "distinct";
    }
}
namespace SMT {
class ExprApp : public Expr {

public:
    Operator op;
    std::vector<std::unique_ptr<Expr>> param_list;

    explicit ExprApp(Operator op, std::vector<std::unique_ptr<Expr>>&& and_list) :
       op(op), param_list (std::move(and_list)) { }
    explicit ExprApp(const ExprApp& expr) : op(expr.op), param_list (std::vector<std::unique_ptr<Expr>>())
    {
        for (auto& exp : expr.param_list)
        {
            param_list.push_back (exp->clone());
        }
    }
    std::string to_smt_lib()const{
        if (op == Operator::And) {
            if (param_list.size() > 1){
                std::vector<std::string> vec;
                for (auto& f: param_list){
                    vec.push_back(f->to_smt_lib());
                }
                auto formulas = boost::algorithm::join(vec, "  ");
                return "(assert ( " + op_str(op) + " " + formulas + "))";
            }
            else{
                return "( assert " + param_list[0] ->to_smt_lib() + " )";
            }
            }
        else {
            if (param_list.size() > 1){
                std::vector<std::string> vec;
                for (auto& f: param_list){
                    vec.push_back(f->to_smt_lib());
                }
                auto formulas = boost::algorithm::join(vec, "  ");
                return " ( " + op_str(op) + " " + formulas + ")";
            }
            else{
                return "(  " + param_list[0] ->to_smt_lib() + " )";
            }
        }
    }
    std::unique_ptr<Expr> clone() const override {
        std::vector<std::unique_ptr<Expr>> and_list_clone;
        and_list_clone.reserve(param_list.size());
        for (auto& child_expr : param_list) {
            and_list_clone.push_back(child_expr->clone());
        }
        return std::make_unique<ExprApp>(op, std::move(and_list_clone));
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }

    bool has_aggregation() const override {
        for (auto& expr : param_list) {
            if (expr->has_aggregation())
                return true;
        }
        return false;
    }

    std::set<VarId> get_all_vars() const override {
        std::set<VarId> res;
        for (auto& expr: param_list) {
            for (auto& var : expr->get_all_vars()) {
                res.insert(var);
            }
        }
        return res;
    }

    std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override {
        std::set<std::tuple<std::string, ObjectId>> res;
        for (auto& expr: param_list) {
            for (auto& var : expr->get_all_attrs()) {
                res.insert(var);
            }
        }
        return res;
    }


    std::set<VarId> get_all_parameter() const override {
        std::set<VarId> res;
        for (auto& expr: param_list) {
            for (auto& var : expr->get_all_parameter()) {
                res.insert(var);
            }
        }
        return res;
    }
};
}
#endif //EXPR_APP_H
