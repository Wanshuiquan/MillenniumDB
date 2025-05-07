//
// Created by heyang-li on 4/23/25.
//

#ifndef TO_APP_H
#define TO_APP_H

#include "query/smt/smt_expr/smt_expr_visitor.h"
#include "query/smt/smt_expr/smt_exprs.h"
#include <cassert>
#include <memory>

namespace SMT {


class ToAPP :public ExprVisitor {
private:
    std::unique_ptr<Expr> current_smt_expr;
    template<typename T>
    bool is_cast_to(const Expr* expr){
        auto new_ptr = dynamic_cast<const T*>(expr);
        return new_ptr != nullptr;
    }

    void flattening_smt_expr(Expr* expr);
    int rank(Expr* expr, int init);

public:
    static std::unique_ptr<Expr> to_app(Expr* expr)
    {
        ToAPP *to_app = new ToAPP();
        expr->accept_visitor(*to_app);
        auto res = std::move(to_app ->current_smt_expr);
        to_app ->  flattening_smt_expr(res.get());
        int val =  to_app -> rank(res.get(), 0);
        assert(to_app -> rank(res.get(), 0) <= 3);
        delete to_app;
        return std::move(res);
    };

    void visit(SMT::ExprVar& expr)
    {
        current_smt_expr = expr.clone();
    }
    void visit(SMT::ExprVarProperty& expr)
    {
        current_smt_expr = expr.clone();
    }
    void visit(SMT::ExprConstant& expr)
    {
        current_smt_expr = expr.clone();
    }
    void visit(SMT::ExprAddition& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Add, std::move(param));
    }
    void visit(SMT::ExprDivision&)        { throw LogicException("visit SMT::ExprDivision not implemented"); }
    void visit(SMT::ExprMultiplication& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Mul, std::move(param));
    }
    void visit(SMT::ExprSubtraction& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Sub, std::move(param));
    }
    void visit(SMT::ExprUnaryMinus& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.expr -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::UniMin, std::move(param));
    }
    void visit(SMT::ExprUnaryPlus&)       { throw LogicException("visit SMT::ExprUnaryPlus not implemented"); }
    void visit(SMT::ExprEquals& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Eq, std::move(param));
    }
    void visit(SMT::ExprGreaterOrEquals& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Gte, std::move(param));
    }
    void visit(SMT::ExprGreater& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Gt, std::move(param));
    }
    void visit(SMT::ExprLessOrEquals& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Lte, std::move(param));
    }
    void visit(SMT::ExprLess& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Lt, std::move(param));
    }
    void visit(SMT::ExprNotEquals& expr)
    {
        std::vector<std::unique_ptr<Expr>> param;
        expr.lhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        expr.rhs -> accept_visitor(*this);
        param.push_back(std::move(current_smt_expr));
        current_smt_expr = std::make_unique<ExprApp>(Operator::Lt, std::move(param));
    }
    void visit(SMT::ExprAnd& expr)             {
        std::vector<std::unique_ptr<Expr>> param;
        for (auto& ele: expr.and_list) {
            ele -> accept_visitor(*this);
            param.push_back(std::move(current_smt_expr));
        }
        current_smt_expr = std::make_unique<ExprApp>(Operator::And, std::move(param));
    }
    void visit(SMT::ExprAttr& expr) {current_smt_expr = expr.clone();}
    void visit(SMT::ExprApp&) {throw LogicException("visit SMT::ExprAttr not implemented");}
};
}




#endif //TO_APP_H
