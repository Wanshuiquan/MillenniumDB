//
// Created by heyang-li on 4/22/25.
//

#include "ir.h"
#include "boost/format.hpp"
#include "boost/beast/http/rfc7230.hpp"

#include <iostream>
#include <sstream>

std::string LinearInequality::to_smt_lib(){
        std::stringstream lhs_param_formula;
        bool lhs_param_true = false;
        for (const auto &key: lhs_param){
            lhs_param_formula << boost::format("(* %1 %2)")%key.first%key.second;
            lhs_param_true = true;
        }


        std::stringstream  lhs_attr_formula;
        bool lhs_attr_true = false;
        for (const auto & key: lhs_attr){
            lhs_param_formula << boost::format("(* %1 %2)")%key.first%key.second;
            lhs_attr_true = true;
        }

        double lhs_cons = std::accumulate(lhs_constant.begin(), lhs_constant.end(), 0.0);

    }

void LinearInequality::visit_lhs_addition(SMT::ExprApp& expr)
{
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(&expr)) {
            auto c = decider.get_const(&expr);
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            lhs_constant.emplace(val);
        }
        if (decider.is_cast_to_attr(&expr)) {
            auto attr_id = decider.get_attr(&expr);
            lhs_attr.emplace(attr_id->to_smt_lib(), 1.0);
        }
        if (decider.is_cast_to_var(&expr)) {
            auto var_id = decider.get_var(&expr);
            lhs_param.emplace(var_id ->to_smt_lib(), 1.0);
        }
        auto param = decider.get_app(p.get());
        visit_lhs_mul(*param);
    }
}

void LinearInequality::visit_rhs_addition(SMT::ExprApp& expr){
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(&expr)) {
            auto c = decider.get_const(&expr);
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            rhs_constant.emplace(val);
        }
        if (decider.is_cast_to_attr(&expr)) {
            auto attr_id = decider.get_attr(&expr);
            rhs_attr.emplace(attr_id->to_smt_lib(), 1.0);
        }
        if (decider.is_cast_to_var(&expr)) {
            auto var_id = decider.get_var(&expr);
            rhs_param.emplace(var_id ->to_smt_lib(), 1.0);
        }
        auto param = decider.get_app(p.get());
        visit_rhs_mul(*param);
    }
}

void LinearInequality::visit_lhs_mul(SMT::ExprApp& expr)
{
    std::vector<double> coff;
    bool attr = false;
    bool var = false;
    bool pure_const = false;
    std::string var_name = "";
    std::string attr_name = "";
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(&expr)) {
            auto c = decider.get_const(&expr);
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            coff.emplace_back(val);
        }
        if (decider.is_cast_to_attr(&expr)) {
            auto attr_id = decider.get_attr(&expr);
            attr_name = attr_id->to_smt_lib();
            attr = true;
        }
        if (decider.is_cast_to_var(&expr)) {
            auto var_id = decider.get_var(&expr);
            attr_name = var_id ->to_smt_lib();
            var = true;
        }
    }

    auto val = std::accumulate(coff.begin(), coff.end(), 1.0, [](double a, double b) { return a * b; });
    if (attr) {
        lhs_attr.emplace(attr_name, val);
    }
    if (var) {
        lhs_param.emplace(var_name, val);
    }
    else {
        lhs_constant.emplace(val);
    }

}

void LinearInequality::visit_rhs_mul(SMT::ExprApp& expr)
{
    std::vector<double> coff;
    bool attr = false;
    bool var = false;
    bool pure_const = false;
    std::string var_name = "";
    std::string attr_name = "";
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(&expr)) {
            auto c = decider.get_const(&expr);
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            coff.emplace_back(val);
        }
        if (decider.is_cast_to_attr(&expr)) {
            auto attr_id = decider.get_attr(&expr);
            attr_name = attr_id->to_smt_lib();
            attr = true;
        }
        if (decider.is_cast_to_var(&expr)) {
            auto var_id = decider.get_var(&expr);
            attr_name = var_id ->to_smt_lib();
            var = true;
        }
    }

    auto val = std::accumulate(coff.begin(), coff.end(), 1.0, [](double a, double b) { return a * b; });
    if (attr) {
        rhs_attr.emplace(attr_name, val);
    }
    if (var) {
        rhs_param.emplace(var_name, val);
    }
    else {
        rhs_constant.emplace(val);
    }

}
void LinearInequality::visit_comparasion_expression(SMT::ExprApp& expr)
{
    auto& exp = *(decider.get_app(&expr));
    Operator op = exp.op;
    switch (op) {
        case Operator::Eq: { assert(exp.get_sort() == Sort::Num); type = InequalityType::Equal; break; }
        case Operator::Neq: { assert(exp.get_sort() == Sort::Num); type = InequalityType::NonEqual; break;}
        case Operator::Gt: { type = InequalityType::Greater; break;}
        case Operator::Gte: { type = InequalityType::GreaterEqual; break;}
        case Operator::Lt: { type = InequalityType::Less; break;}
        case Operator::Lte: { type = InequalityType::LessEqual; break;}
        default: {
            throw std::logic_error("Unknown operator in comparasion_expression");
        }
    }
    auto lhs = decider.get_app(exp.param_list[0].get());
    visit_lhs_addition(*lhs);
    auto rhs = decider.get_app(exp.param_list[1].get());
    visit_rhs_addition(*rhs);
}


void LinearInequality::build_map(SMT::Expr& expr) {
    if (decider.is_cast_to_const(&expr)) {
        return;
    }
    visit_comparasion_expression(*(decider.get_app(&expr)));
}

void LinearInequality::reduce_to_normal_form()
{
   for (auto& p: lhs_attr) {
       auto key = p.first;
       auto val = p.second;
       lhs_attr.erase(key);
       rhs_attr.emplace(key, -1* val);
   }
    for (auto& p: rhs_param) {
        auto key = p.first;
        auto val = p.second;
        rhs_param.erase(key);
        lhs_param.emplace(key, -1* val);
    }

    auto lhs_sum = std::accumulate(lhs_constant.begin(), lhs_constant.end(), 0.0);
    auto rhs_sum = std::accumulate(rhs_constant.begin(), rhs_constant.end(), 0.0);
    rhs_constant.emplace(rhs_sum - lhs_sum);
}
