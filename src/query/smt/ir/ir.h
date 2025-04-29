#pragma once
#include "query/smt/smt_expr/smt_exprs.h"
#include "query/smt/smt_expr/smt_expr_visitor.h"
#include <unordered_set>



enum class InequalityType {
    LessEqual,     // <=
    GreaterEqual,  // >=
    Less,          // <
    Greater,       // >
    Equal,          // ==
    NonEqual
};

struct TypeDecider {
    // type decider
    template<typename T>
    bool is_cast_to(SMT::Expr* expr)
    {
        auto ptr = dynamic_cast<T*>(expr);
        return ptr != nullptr;
    }

    bool   is_cast_to_app(SMT::Expr* expr)
    {
        return is_cast_to<SMT::ExprApp>(expr);
    }

    bool   is_cast_to_var(SMT::Expr* expr)
    {
        return is_cast_to<SMT::ExprVar>(expr);
    }

    bool   is_cast_to_attr(SMT::Expr* expr)
    {
        return is_cast_to<SMT::ExprAttr>(expr);
    }
    bool   is_cast_to_const(SMT::Expr* expr)
    {
        return is_cast_to<SMT::ExprConstant>(expr);
    }

    // dynamic cast to subtypes
    template<typename T>
    T* cast_to(SMT::Expr* expr)
    {
        assert(is_cast_to<T>(expr));
        return dynamic_cast<T*>(expr);
    }

    SMT::ExprApp*  get_app(SMT::Expr* expr)
    {
        return cast_to<SMT::ExprApp>(expr);
    }

    SMT::ExprVar*  get_var(SMT::Expr* expr)
    {
        return cast_to<SMT::ExprVar>(expr);
    }

    SMT::ExprAttr*  get_attr(SMT::Expr* expr)
    {
        return cast_to<SMT::ExprAttr>(expr);
    }
    SMT::ExprConstant*  get_const(SMT::Expr* expr)
    {
        return cast_to<SMT::ExprConstant>(expr);
    }
    bool is_comparison_expression(SMT::Expr* expr)
    {
        if (is_cast_to_app(expr)) {
            auto app = get_app(expr);
            auto op = app->op;
            return op == Operator::Eq || op == Operator::Neq || op == Operator::Gt || op == Operator::Lt || op == Operator::Gte || op == Operator::Lte;
        }
        else {
            return false;
        }
    }
};


class LinearInequality {
    std::unordered_map<std::string, double> lhs_param; // e.g., { "x": 3, "y": 2 }
    std::unordered_map<std::string, double> lhs_attr;
    std::unordered_set<double> lhs_constant;
    std::unordered_map<std::string, double> rhs_param;
    std::unordered_map<std::string, double> rhs_attr;
    std::unordered_set<double> rhs_constant;
    InequalityType type; // Inequality type (<=, >=, etc.)
    TypeDecider decider;
public:
    LinearInequality(SMT::ExprApp& expr)
    {
        assert(decider.is_comparison_expression(&expr));

    }
    std::string to_smt_lib();
    void build_map(SMT::Expr&);
    void visit_comparasion_expression(SMT::ExprApp&);
    void visit_lhs_addition(SMT::ExprApp&);
    void visit_rhs_addition(SMT::ExprApp&);
    void visit_lhs_mul(SMT::ExprApp&);
    void visit_rhs_mul(SMT::ExprApp&);
    void reduce_to_normal_form();

};

class Conjunction {
    TypeDecider decider;
public:
    std::vector<LinearInequality> expressions;



};

