#pragma once
#include "query/smt/smt_expr/smt_exprs.h"
#include "query/smt/smt_expr/smt_expr_visitor.h"
#include <unordered_set>
#include <variant>


enum class InequalityType {
    LessEqual,     // <=
    GreaterEqual,  // >=
    Less,          // <
    Greater,       // >
    Equal,          // ==
    NonEqual
};

inline   std::string op_tostr(InequalityType ty){
    switch (ty) {
        case InequalityType::LessEqual: return "<=";    // <=
        case InequalityType::GreaterEqual: return ">=";  // >=
        case InequalityType::Less: return "<";          // <
        case InequalityType::Greater: return ">";       // >
        case InequalityType::Equal: return "=";          // =
        case InequalityType::NonEqual: return "distinct";
    }
}
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
        switch (expr.op) {
            case Operator::Eq: type = InequalityType::Equal; break;
            case Operator::Neq: type = InequalityType::NonEqual; break;
            case Operator::Gt: type = InequalityType::Greater; break;
            case Operator::Lt: type = InequalityType::Less; break;
            case Operator::Gte: type = InequalityType::GreaterEqual; break;
            case Operator::Lte: type = InequalityType::LessEqual; break;
            default: throw std::runtime_error("Not Support");
        }

        build_map(expr);
        reduce_to_normal_form();

    }
    std::string to_reduced_smt_lib();
    void build_map(SMT::Expr&);
    void visit_comparison_expression(SMT::ExprApp&);
    void visit_lhs_addition(SMT::ExprApp&);
    void visit_rhs_addition(SMT::ExprApp&);
    void visit_lhs_mul(SMT::ExprApp&);
    void visit_rhs_mul(SMT::ExprApp&);
    void reduce_to_normal_form();
    std::unique_ptr<SMT::Expr> to_reduced_ast();
    static void reduce(SMT::Expr& expr)
    {
        TypeDecider decider;
        assert(decider.is_cast_to_app(&expr));
        auto appli = decider.get_app(&expr);
        for (auto& param: appli -> param_list) {
            if (decider.is_cast_to_app(param.get())) {
                const auto app = decider.get_app(param.get());
                if (app->get_sort() == Sort::Num) {
                    LinearInequality exp(*app);
                    param = exp.to_reduced_ast();
                }

            }
        }
    }
};




