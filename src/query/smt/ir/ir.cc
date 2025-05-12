//
// Created by heyang-li on 4/22/25.
//

#include "ir.h"
#include "boost/format.hpp"
#include <sstream>


std::string LinearInequality::to_reduced_smt_lib(){
        assert(lhs_attr.empty() && rhs_param.empty() && lhs_constant.empty());
        std::stringstream lhs_param_formula;
        for (const auto &key: lhs_param){
            lhs_param_formula << boost::format("(* %1 %2)")%key.first%key.second;
        }
        std::stringstream  rhs_attr_formula;
        bool rhs_attribute_exists = false;
        for (const auto & key: lhs_attr){
            rhs_attr_formula << boost::format("(* %1 %2)")%key.first%key.second;
            rhs_attribute_exists = true;
        }
        double rhs_cons = std::accumulate(rhs_constant.begin(), lhs_constant.end(), 0.0);
        std::string rhs;
        if (rhs_attribute_exists){
            rhs = (boost::format("(+ %1 %2)")%rhs_attr_formula.str()%rhs_cons).str();
        }
        else{
            rhs = std::to_string(rhs_cons);
        }
        std::string lhs = (boost::format("(+ %1)")%lhs_param_formula.str()).str();
        return (boost::format("(%1 %2 %3)")% op_tostr(type)%lhs%rhs).str();
    }

void LinearInequality::visit_lhs_addition(SMT::ExprApp& expr)
{
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(p.get())) {
            auto c = decider.get_const(p.get());
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            lhs_constant.emplace(val);
        }
        else if (decider.is_cast_to_attr(p.get())) {
            auto attr_id = decider.get_attr(p.get());
            lhs_attr.emplace(attr_id->to_smt_lib(), 1.0);
        }
        else if (decider.is_cast_to_var(p.get())) {
            auto var_id = decider.get_var(p.get());
            lhs_param.emplace(var_id ->to_smt_lib(), 1.0);
        }
        else {
            auto param = decider.get_app(p.get());
            visit_lhs_mul(*param);
        }

    }
}

void LinearInequality::visit_rhs_addition(SMT::ExprApp& expr){
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(p.get())) {
            auto c = decider.get_const(p.get());
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            rhs_constant.emplace(val);
        }
        else if (decider.is_cast_to_attr(p.get())) {
            auto attr_id = decider.get_attr(p.get());
            rhs_attr.emplace(attr_id->to_smt_lib(), 1.0);
        }
        else if (decider.is_cast_to_var(p.get())) {
            auto var_id = decider.get_var(p.get());
            rhs_param.emplace(var_id ->to_smt_lib(), 1.0);
        }
        else {
            auto param = decider.get_app(p.get());
            visit_rhs_mul(*param);
        }
    }
}

void LinearInequality::visit_lhs_mul(SMT::ExprApp& expr)
{
    std::vector<double> coff;
    bool attr = false;
    bool var = false;
    bool pure_const = false;
    std::string var_name;
    std::string attr_name;
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(p.get())) {
            auto c = decider.get_const(p.get());
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            coff.emplace_back(val);
        }
        if (decider.is_cast_to_attr(p.get())) {
            auto attr_id = decider.get_attr(p.get());
            attr_name = attr_id->to_smt_lib();
            attr = true;
        }
        if (decider.is_cast_to_var(p.get())) {
            auto var_id = decider.get_var(p.get());
            var_name = var_id ->to_smt_lib();
            var = true;
        }
    }

    auto val = std::accumulate(coff.begin(), coff.end(), 1.0, [](double a, double b) { return a * b; });
    if (attr) {
        lhs_attr.emplace(attr_name, val);
    }
    else if (var) {
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
    std::string var_name;
    std::string attr_name;
    for (auto&p : expr.param_list){
        if (decider.is_cast_to_const(p.get())) {
            auto c = decider.get_const(p.get());
            std::variant<double, std::string, bool> obj = decode_mask(c->value);
            auto val = *std::get_if<double>(&obj);
            coff.emplace_back(val);
        }
        if (decider.is_cast_to_attr(p.get())) {
            auto attr_id = decider.get_attr(p.get());
            attr_name = attr_id->to_smt_lib();
            attr = true;
        }
        if (decider.is_cast_to_var(p.get())) {
            auto var_id = decider.get_var(p.get());
            var_name = var_id ->to_smt_lib();
            var = true;
        }
    }

    auto val = std::accumulate(coff.begin(), coff.end(), 1.0, [](double a, double b) { return a * b; });
    if (attr) {
        rhs_attr.emplace(attr_name, val);
    }
    else  if (var) {
        rhs_param.emplace(var_name, val);
    }
    else {
        rhs_constant.emplace(val);
    }

}
void LinearInequality::visit_comparison_expression(SMT::ExprApp& expr)
{
    Operator op = expr.op;
    switch (op) {
        case Operator::Eq: { assert(expr.get_sort() == Sort::Num); type = InequalityType::Equal; break; }
        case Operator::Neq: { assert(expr.get_sort() == Sort::Num); type = InequalityType::NonEqual; break;}
        case Operator::Gt: { type = InequalityType::Greater; break;}
        case Operator::Gte: { type = InequalityType::GreaterEqual; break;}
        case Operator::Lt: { type = InequalityType::Less; break;}
        case Operator::Lte: { type = InequalityType::LessEqual; break;}
        default: {
            throw std::logic_error("Unknown operator in comparison_expression");
        }
    }

    auto lhs = expr.param_list[0].get();
    auto rhs = expr.param_list[1].get();
    if (decider.is_cast_to_const(lhs)) {

        auto c = decider.get_const(lhs);
        std::variant<double, std::string, bool> obj = decode_mask(c->value);
        auto val = *std::get_if<double>(&obj);
        lhs_constant.emplace(val);
    }
    else if (decider.is_cast_to_attr(lhs)) {
        auto attr_id = decider.get_attr(lhs);
        lhs_attr.emplace(attr_id->to_smt_lib(), 1.0);
    }
    else if (decider.is_cast_to_var(lhs)) {
        auto var_id = decider.get_var(lhs);
        lhs_param.emplace(var_id ->to_smt_lib(), 1.0);
    }
    else {
        auto lhs_compare = decider.get_app(lhs);
        visit_lhs_addition(*lhs_compare);
    }
    if (decider.is_cast_to_const(rhs)) {

        auto c = decider.get_const(rhs);
        std::variant<double, std::string, bool> obj = decode_mask(c->value);
        auto val = *std::get_if<double>(&obj);
        rhs_constant.emplace(val);
    }
    else if (decider.is_cast_to_attr(rhs)) {
        auto attr_id = decider.get_attr(rhs);
        rhs_attr.emplace(attr_id->to_smt_lib(), 1.0);
    }
    else if (decider.is_cast_to_var(rhs)) {
        auto var_id = decider.get_var(rhs);
        rhs_param.emplace(var_id ->to_smt_lib(), 1.0);
    }
    else {
        auto rhs_compare = decider.get_app(rhs);
        visit_rhs_addition(*rhs_compare);
    }
}


void LinearInequality::build_map(SMT::Expr& expr) {
    if (decider.is_cast_to_const(&expr)) {
        return;
    }
    visit_comparison_expression(*(decider.get_app(&expr)));
}

void LinearInequality::reduce_to_normal_form()
{
   for (auto& p: lhs_attr) {
       auto key = p.first;
       auto val = p.second;
       rhs_attr.emplace(key, -1* val);
   }
    lhs_attr.clear();
    for (auto& p: rhs_param) {
        auto key = p.first;
        auto val = p.second;
        lhs_param.emplace(key, -1* val);
    }
    rhs_param.clear();
    auto lhs_sum = std::accumulate(lhs_constant.begin(), lhs_constant.end(), 0.0);
    lhs_constant.clear();
    auto rhs_sum = std::accumulate(rhs_constant.begin(), rhs_constant.end(), 0.0);
    rhs_constant.emplace(rhs_sum - lhs_sum);
}

std::unique_ptr<SMT::Expr> LinearInequality::to_reduced_ast()
{
    assert(lhs_attr.empty() && rhs_param.empty() && lhs_constant.empty());
    std::vector<std::unique_ptr<SMT::Expr>> lhs_param_list;
    for (const auto &key: lhs_param){
         std::vector<std::unique_ptr<SMT::Expr>> param_list;
         param_list.push_back(std::make_unique<SMT::ExprConstant>(QuadObjectId::get_value(std::to_string(key.second))));
         param_list.push_back(std::make_unique<SMT::ExprVar>(get_query_ctx().get_or_create_var(key.first)));
         lhs_param_list.push_back(std::make_unique<SMT::ExprApp>(Operator::Mul, std::move(param_list)));
    }
    std::vector<std::unique_ptr<SMT::Expr>> rhs_param_list;
    for (const auto &key: rhs_attr){
        std::vector<std::unique_ptr<SMT::Expr>> param_list;
        param_list.push_back(std::make_unique<SMT::ExprConstant>(QuadObjectId::get_value(std::to_string(key.second))));
        param_list.push_back(std::make_unique<SMT::ExprVar>(get_query_ctx().get_or_create_var(key.first)));
        rhs_param_list.push_back(std::make_unique<SMT::ExprApp>(Operator::Mul, std::move(param_list)));
    }
    double rhs_cons = std::accumulate(rhs_constant.begin(), rhs_constant.end(), 0.0);
    rhs_param_list.push_back(std::make_unique<SMT::ExprConstant>(QuadObjectId::get_value(std::to_string(rhs_cons))));
    std::unique_ptr<SMT::Expr> lhs;
    std::unique_ptr<SMT::Expr> rhs;
    if (lhs_param_list.size() == 1) {
        lhs = std::move(lhs_param_list[0]);
    }
    else {
        lhs = std::make_unique<SMT::ExprApp>(Operator::Add, std::move(lhs_param_list));
    }
    if (rhs_param_list.size() == 1) {
        rhs = std::move(rhs_param_list[0]);
    }
    else {
        rhs = std::make_unique<SMT::ExprApp>(Operator::Add, std::move(rhs_param_list));
    }    Operator op;
    switch (type) {
        case InequalityType::Equal: op = Operator::Eq; break;
        case InequalityType::NonEqual: op = Operator::Neq; break;
        case InequalityType::Greater: op = Operator::Gt; break;
        case InequalityType::GreaterEqual: op = Operator::Gte; break;
        case InequalityType::Less: op = Operator::Lt; break;
        case InequalityType::LessEqual: op = Operator::Lte; break;
        default: throw std::logic_error("Unknown inequality type");
    }
    std::vector<std::unique_ptr<SMT::Expr>> p;
    p.push_back(std::move(lhs));
    p.push_back(std::move(rhs));
    auto res = std::make_unique<SMT::ExprApp>(op, std::move(p));
    return std::move(res);
}


void LinearInequality::convert(LinearInequality& f, double quotient)
{
    for (auto& p: f.lhs_param) {
        auto key = p.first;
        auto val = p.second;
        f.lhs_param[key] = val * quotient;
    }
    for (auto& p: f.rhs_attr) {
        auto key = p.first;
        auto val = p.second;
        f.rhs_attr[key]= val* quotient;
    }
    std::for_each(f.rhs_constant.begin(), f.rhs_constant.end(), [quotient](const double  p){return p * quotient;});
    if (quotient < 0){
        if (f.type == InequalityType::GreaterEqual) {f.type = InequalityType::LessEqual; }
        if (f.type == InequalityType::LessEqual) {f.type = InequalityType::GreaterEqual; }
    }
}



std::optional<double> LinearInequality::quotient_lhs(LinearInequality& op1, LinearInequality& op2)
{
    // only work for optimized expressions; 
    std::vector<std::string> op1_lhs_keys;
    std::transform(op1.lhs_param.begin(), op1.lhs_param.end(), std::back_inserter(op1_lhs_keys), [](auto& p){return p.first;});
    std::vector<std::string> op2_lhs_keys;
    std::transform(op2.lhs_param.begin(), op2.lhs_param.end(), std::back_inserter(op2_lhs_keys), [](auto& p){return p.first;});


    if (op1_lhs_keys != op2_lhs_keys) {
        return std::nullopt;
    }

    double ratio = -1;

    // Check parameter coefficients
    for (const auto& key : op1_lhs_keys) {
        double coef1 = op1.lhs_param.at(key);
        double coef2 = op2.lhs_param.at(key);
        if (coef2 == 0)
            return std::nullopt;
        double current_ratio = coef1 / coef2;
        if (ratio == -1)
            ratio = current_ratio;
        else
            if (ratio != current_ratio)
                return std::nullopt;
    }
    return ratio;
}
