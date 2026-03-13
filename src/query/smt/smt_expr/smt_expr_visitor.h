//
// Created by heli on 8/23/24.
//

#pragma once

#include "query/exceptions.h"

namespace SMT {
class ExprVar;
class ExprVarProperty;
class ExprConstant;
class ExprAddition;
class ExprDivision;
class ExprMultiplication;
class ExprSubtraction;
class ExprUnaryMinus;
class ExprUnaryPlus;
class ExprEquals;
class ExprGreaterOrEquals;
class ExprGreater;
class ExprLessOrEquals;
class ExprLess;
class ExprNotEquals;
    class ExprAttr;
class ExprAnd;





class ExprVisitor {
public:
    virtual ~ExprVisitor() = default;

    virtual void visit(SMT::ExprVar&)             { throw LogicException("visit SMT::ExprVar not implemented"); }
    virtual void visit(SMT::ExprVarProperty&)     { throw LogicException("visit SMT::ExprVarProperty not implemented"); }
    virtual void visit(SMT::ExprConstant&)        { throw LogicException("visit SMT::ExprConstant not implemented"); }
    virtual void visit(SMT::ExprAddition&)        { throw LogicException("visit SMT::ExprAddition not implemented"); }
    virtual void visit(SMT::ExprDivision&)        { throw LogicException("visit SMT::ExprDivision not implemented"); }
    virtual void visit(SMT::ExprMultiplication&)  { throw LogicException("visit SMT::ExprMultiplication not implemented"); }
    virtual void visit(SMT::ExprSubtraction&)     { throw LogicException("visit SMT::ExprSubtraction not implemented"); }
    virtual void visit(SMT::ExprUnaryMinus&)      { throw LogicException("visit SMT::ExprUnaryMinus not implemented"); }
    virtual void visit(SMT::ExprUnaryPlus&)       { throw LogicException("visit SMT::ExprUnaryPlus not implemented"); }
    virtual void visit(SMT::ExprEquals&)          { throw LogicException("visit SMT::ExprEquals not implemented"); }
    virtual void visit(SMT::ExprGreaterOrEquals&) { throw LogicException("visit SMT::ExprGreaterOrEquals not implemented"); }
    virtual void visit(SMT::ExprGreater&)         { throw LogicException("visit SMT::ExprGreater not implemented"); }
    virtual void visit(SMT::ExprLessOrEquals&)    { throw LogicException("visit SMT::ExprLessOrEquals not implemented"); }
    virtual void visit(SMT::ExprLess&)            { throw LogicException("visit SMT::ExprLess not implemented"); }
    virtual void visit(SMT::ExprNotEquals&)       { throw LogicException("visit SMT::ExprNotEquals not implemented"); }
    virtual void visit(SMT::ExprAnd&)             { throw LogicException("visit SMT::ExprAnd not implemented"); }
    virtual void visit(SMT::ExprAttr&) {throw LogicException("visit SMT::ExprAttr not implemented");}
};
}