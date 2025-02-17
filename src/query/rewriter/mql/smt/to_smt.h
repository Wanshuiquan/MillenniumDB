//
// Created by heli on 8/23/24.
//
#pragma once

#include <set>

#include "query/smt/smt_expr/smt_exprs.h"
#include "query/parser/expr/expr_visitor.h"
#include "query/parser/expr/expr.h"
#include "query/parser/op/op_visitor.h"
#include "query/var_id.h"
#include "graph_models/quad_model/quad_object_id.h"
namespace MQL{
    class ToSMT : public ExprVisitor {
    public:
        std::unique_ptr<SMT::Expr> current_smt_expr;

        void visit(ExprConstant& expr) override;
        void visit(ExprVar&) override;
        void visit(ExprVarProperty&) override;
        void visit(ExprAddition&) override;
        void visit(ExprDivision&) override{throw std::runtime_error("not implemented");}
        void visit(ExprModulo&) override{throw std::runtime_error("not implemented");}
        void visit(ExprMultiplication&) override;
        void visit(ExprSubtraction&) override;
        void visit(ExprUnaryMinus&) override;
        void visit(ExprUnaryPlus&) override;
        void visit(ExprEquals&) override;
        void visit(ExprGreaterOrEquals&) override;
        void visit(ExprGreater&) override;
        void visit(ExprIs&) override;
        void visit(ExprLessOrEquals&) override;
        void visit(ExprLess&) override;
        void visit(ExprNotEquals&) override;
        void visit(ExprAnd&) override;
        void visit(ExprNot&) override{throw std::runtime_error("not implemented");}
        void visit(ExprOr&) override{throw std::runtime_error("not implemented");}

        void visit(ExprAggAvg&) override{throw std::runtime_error("not implemented");}
        void visit(ExprAggCountAll&) override{throw std::runtime_error("not implemented");}
        void visit(ExprAggCount&) override{throw std::runtime_error("not implemented");}
        void visit(ExprAggMax&) override{throw std::runtime_error("not implemented");}
        void visit(ExprAggMin&)override {throw std::runtime_error("not implemented");}
        void visit(ExprAggSum&) override{throw std::runtime_error("not implemented");}

        std::unique_ptr<SMT::Expr> get_smt_expr() {return std::unique_ptr<SMT::Expr>(current_smt_expr -> clone());}

    };
}