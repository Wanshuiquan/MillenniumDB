//
// Created by heli on 8/24/24.
//

#include "smt_expr_printer.h"
#include "smt_exprs.h"
#include <boost/algorithm/string/join.hpp>

using namespace SMT;


void SmtPrinter::visit(ExprVar& expr) {
    os << '?' << get_query_ctx().get_var_name(expr.var);
}

void SmtPrinter::visit(SMT::ExprAttr& expr)
{
    os << expr.name;
}


void SmtPrinter::visit(ExprVarProperty& expr) {
    os << '?' << get_query_ctx().get_var_name(expr.var_with_property);
}


void SmtPrinter::visit(ExprConstant& expr) {
    os  << expr.to_smt_lib();
}


void SmtPrinter::visit(ExprAddition& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " + ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprDivision& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " / ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}





void SmtPrinter::visit(ExprMultiplication& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " * ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprSubtraction& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " - ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprUnaryMinus& expr) {
    os << '-';
    expr.expr->accept_visitor(*this);
}


void SmtPrinter::visit(ExprUnaryPlus& expr) {
    os << '+';
    expr.expr->accept_visitor(*this);
}


void SmtPrinter::visit(ExprEquals& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " == ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprGreaterOrEquals& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " >= ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprGreater& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " > ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}





void SmtPrinter::visit(ExprLessOrEquals& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " <= ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprLess& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " < ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprNotEquals& expr) {
    os << '(';
    expr.lhs->accept_visitor(*this);
    os << " != ";
    expr.rhs->accept_visitor(*this);
    os << ')' ;
}


void SmtPrinter::visit(ExprAnd& expr) {
    os << '(';
    expr.and_list[0]->accept_visitor(*this);
    for (size_t i = 1; i < expr.and_list.size(); i++) {
        os << " AND ";
        expr.and_list[i]->accept_visitor(*this);
    }
    os << ')' ;
}