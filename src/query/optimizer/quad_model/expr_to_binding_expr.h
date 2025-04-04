#pragma once

#include <optional>

#include "query/executor/binding_iter/binding_expr/binding_expr.h"
#include "query/optimizer/quad_model/binding_iter_constructor.h"
#include "query/parser/expr/expr.h"
#include "query/parser/expr/expr_visitor.h"

namespace MQL {

class BindingIterConstructor;

// This visitor returns nullptr if condition is pushed outside
class ExprToBindingExpr : public ExprVisitor {
public:
    BindingIterConstructor* bic = nullptr;
    std::vector<PropertyTypeConstraint> fixed_types_properties;

    // In expressions like "<expressions> AS <var>", as_var is <var>
    const std::optional<VarId> as_var;

    // Where result will be stored
    std::unique_ptr<BindingExpr> tmp;

    // Has to be true while visiting something inside of an aggregation
    // and be false otherwise
    bool inside_aggregation = false;

    ExprToBindingExpr(std::vector<PropertyTypeConstraint>& fixed_types_properties) :
        bic(nullptr),
        fixed_types_properties(fixed_types_properties)
    { }

    // For Aggregations in RETURN, ORDER BY
    // (for now the language only permits Agg Functions in them)
    ExprToBindingExpr(BindingIterConstructor* _bic, std::optional<VarId> as_var) :
        bic(_bic),
        fixed_types_properties(_bic->fixed_types_properties),
        as_var(as_var)
    { }

    void visit(ExprAggAvg&) override;
    void visit(ExprAggCountAll&) override;
    void visit(ExprAggCount&) override;
    void visit(ExprAggMax&) override;
    void visit(ExprAggMin&) override;
    void visit(ExprAggSum&) override;

    void visit(ExprVar&) override;
    void visit(ExprVarProperty&) override;
    void visit(ExprConstant&) override;
    void visit(ExprAddition&) override;
    void visit(ExprDivision&) override;
    void visit(ExprModulo&) override;
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
    void visit(ExprNot&) override;
    void visit(ExprOr&) override;
    void visit(ExprRegex&) override;
    void visit(ExprTensorDistance&) override;
    void visit(ExprTextSearch&) override;

private:

    template<typename AggType, class ... Args>
    void check_and_make_aggregate(Expr*, Args&&... args);
};
} // namespace MQL
