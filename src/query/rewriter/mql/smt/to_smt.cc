//
// Created by heli on 8/23/24.
//
#include "to_smt.h"
#include "query/parser/expr/mql_exprs.h"

using namespace MQL;
void ToSMT::visit(ExprConstant& expr) {
    current_smt_expr =  std::make_unique<SMT::ExprConstant>(expr.value);
}

void ToSMT::visit(ExprVar& expr){
    auto name = get_query_ctx().get_var_name(expr.var);
    if (name.find("id")!=std::string::npos)
    {
        auto attr_name =  name.erase(0,2);
        auto quad_obj = ObjectId(QuadObjectId::get_string(attr_name));
        current_smt_expr = std::make_unique<SMT::ExprAttr>(quad_obj, name);
    }
    else
    {
        current_smt_expr =  std::make_unique<SMT::ExprVar>(expr.var);
    }
}
void ToSMT::visit(ExprVarProperty& expr){
    current_smt_expr = std::make_unique<SMT::ExprVarProperty>(expr.var_without_property, expr.key, expr.var_with_property);
}
void ToSMT::visit(ExprAddition& expr) {
    auto lhs =  expr.lhs.get();
    lhs->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprAddition>(std::move(l), std::move(r));
}

void ToSMT::visit(ExprMultiplication& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprMultiplication>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprSubtraction& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprSubtraction>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprUnaryMinus& expr) {
    auto exp = expr.expr.get();
    exp->accept_visitor(*this);
    current_smt_expr = std::make_unique<SMT::ExprUnaryMinus>(std::move(current_smt_expr));
}
void ToSMT::visit(ExprUnaryPlus& expr) {
    auto exp = expr.expr.get();
    exp->accept_visitor(*this);
    current_smt_expr = std::make_unique<SMT::ExprUnaryPlus>(std::move(current_smt_expr));
}
void ToSMT::visit(ExprEquals& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprEquals>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprGreaterOrEquals& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprGreaterOrEquals>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprGreater& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprGreater>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprIs&) {
    throw std::runtime_error("not implemented");
}
void ToSMT::visit(ExprLessOrEquals& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprLessOrEquals>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprLess& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprLess>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprNotEquals& expr) {
    auto lhs =  expr.lhs.get();
    auto rhs =  expr.rhs.get();
    rhs ->accept_visitor(*this);
    auto r = std::move(current_smt_expr);
    lhs ->accept_visitor(*this);
    auto l = std::move(current_smt_expr);
    current_smt_expr = std::make_unique<SMT::ExprNotEquals>(std::move(l), std::move(r));
}
void ToSMT::visit(ExprAnd& expr) {
    auto and_list = std::move(expr.and_list);
    auto novi_and_list = std::vector<std::unique_ptr<SMT::Expr>>();
    for (auto& l : and_list) {
        l -> accept_visitor(*this);
        novi_and_list.push_back(std::move(current_smt_expr));
    }
    current_smt_expr = std::make_unique<SMT::ExprAnd>(std::move(novi_and_list));
}