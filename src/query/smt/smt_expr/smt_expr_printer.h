//
// Created by heli on 8/24/24.
//

#ifndef SMT_EXPR_PRINTER_H
#define SMT_EXPR_PRINTER_H
#include "smt_expr.h"
#include "smt_expr_visitor.h"

namespace SMT{

    class SmtPrinter : public ExprVisitor {
    public:
        std::ostream& os;
        SmtPrinter(std::ostream& os) : os(os) {}
        ~SmtPrinter() {}
        virtual void visit(SMT::ExprVar&)             override;
        virtual void visit(SMT::ExprVarProperty&)     override;
        virtual void visit(SMT::ExprConstant&)        override;
        virtual void visit(SMT::ExprAddition&)        override;
        virtual void visit(SMT::ExprDivision&)        override;
        virtual void visit(SMT::ExprMultiplication&)  override;
        virtual void visit(SMT::ExprSubtraction&)     override;
        virtual void visit(SMT::ExprUnaryMinus&)      override;
        virtual void visit(SMT::ExprUnaryPlus&)       override;
        virtual void visit(SMT::ExprEquals&)          override;
        virtual void visit(SMT::ExprGreaterOrEquals&) override;
        virtual void visit(SMT::ExprGreater&)         override;
        virtual void visit(SMT::ExprLessOrEquals&)    override;
        virtual void visit(SMT::ExprLess&)            override;
        virtual void visit(SMT::ExprNotEquals&)      override;
        virtual void visit(SMT::ExprAnd&)             override;
        virtual void visit(SMT::ExprAttr&) override;

    };
}


#endif //SMT_EXPR_PRINTER_H
