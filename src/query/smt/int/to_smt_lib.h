//
// Created by heyang-li on 4/27/26.
//

#ifndef MILLENNIUMDB_TO_SMT_LIB_H
#define MILLENNIUMDB_TO_SMT_LIB_H

#include <string>
#include <vector>

#include <boost/algorithm/string/join.hpp>
#include "int_smt_operations.h"
#include "query/query_context.h"
#include "query/smt/smt_expr/smt_expr_visitor.h"
#include "query/smt/smt_expr/smt_exprs.h"

namespace SMT {

class ToSMTLibInt : public ExprVisitor {
    std::string smt_formula;

    std::string convert(Expr& expr) {
        ToSMTLibInt sub;
        expr.accept_visitor(sub);
        return sub.smt_formula;
    }

public:
    std::string get_smt_formula() const {
        return smt_formula;
    }

    static std::string convert_expr(Expr& expr) {
        ToSMTLibInt visitor;
        expr.accept_visitor(visitor);
        return visitor.smt_formula;
    }

    void visit(ExprVar& expr) override {
        smt_formula = get_query_ctx().get_var_name(expr.var);
    }

    void visit(ExprVarProperty&) override {
        throw std::runtime_error("Not Support");
    }

    void visit(ExprConstant& expr) override {
        if (expr.value.is_true()) {
            smt_formula = "true";
        } else if (expr.value.is_false()) {
            smt_formula = "false";
        } else {
            Result obj = decode_mask(expr.value);
            auto str_val = std::get_if<std::string>(&obj);
            if (str_val != nullptr) {
                smt_formula = "\"" + *str_val + "\"";
            } else {
                smt_formula = std::to_string(*std::get_if<int64_t>(&obj));
            }
        }
    }

    void visit(ExprAddition& expr) override {
        smt_formula = "( + " + convert(*expr.lhs) + "   " + convert(*expr.rhs) + ")";
    }

    void visit(ExprSubtraction& expr) override {
        smt_formula = "( - " + convert(*expr.lhs) + "  " + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprMultiplication& expr) override {
        smt_formula = " (  * " + convert(*expr.lhs) + "  " + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprDivision& expr) override {
        smt_formula = " ( / " + convert(*expr.lhs) + "  " + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprUnaryMinus&) override {
        throw std::runtime_error("Not Support");
    }

    void visit(ExprUnaryPlus&) override {
        throw std::runtime_error("Not Support");
    }

    void visit(ExprEquals& expr) override {
        smt_formula = "( = " + convert(*expr.lhs) + "  " + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprNotEquals& expr) override {
        smt_formula = "( distinct" + convert(*expr.lhs) + "  " + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprGreater& expr) override {
        auto add_epsilon = "  (+ epsilon   " + convert(*expr.rhs) + " ) ";
        smt_formula = "( >=  " + convert(*expr.lhs) + add_epsilon + ")";
    }

    void visit(ExprGreaterOrEquals& expr) override {
        smt_formula = "( >= " + convert(*expr.lhs) + "  " + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprLess& expr) override {
        auto add_epsilon = "  (+ epsilon   " + convert(*expr.lhs) + " ) ";
        smt_formula = "( <= " + add_epsilon + convert(*expr.rhs) + " ) ";
    }

    void visit(ExprLessOrEquals& expr) override {
        smt_formula = "( <= " + convert(*expr.lhs) + "  " + convert(*expr.rhs) + ")";
    }

    void visit(ExprAnd& expr) override {
        if (expr.and_list.size() > 1) {
            std::vector<std::string> vec;
            for (auto& f : expr.and_list) {
                vec.push_back(convert(*f));
            }
            auto formulas = boost::algorithm::join(vec, "");
            smt_formula = "(assert ( and" + formulas + "))";
        } else {
            smt_formula = "( assert " + convert(*expr.and_list[0]) + " )";
        }
    }

    void visit(ExprAttr& expr) override {
        smt_formula = expr.name;
    }
};

} // namespace SMT

#endif //MILLENNIUMDB_TO_SMT_LIB_H
