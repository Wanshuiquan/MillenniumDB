#pragma once

#include <memory>

#include "graph_models/gql/conversions.h"
#include "query/exceptions.h"
#include "query/executor/binding_iter/binding_expr/binding_expr.h"

namespace GQL {
class BindingExprDivision : public BindingExpr {
public:
    std::unique_ptr<BindingExpr> lhs;
    std::unique_ptr<BindingExpr> rhs;

    BindingExprDivision(std::unique_ptr<BindingExpr> lhs, std::unique_ptr<BindingExpr> rhs) :
        lhs(std::move(lhs)),
        rhs(std::move(rhs))
    { }

    ObjectId eval(const Binding& binding) override
    {
        auto lhs_oid = lhs->eval(binding);
        auto rhs_oid = rhs->eval(binding);

        auto optype = GQL::Conversions::calculate_optype(lhs_oid, rhs_oid);

        switch (optype) {
        case GQL::Conversions::OPTYPE_INTEGER: {
            // In SPARQL-1.1 integer division is done using decimals, and the result is a decimal
            auto rhs = GQL::Conversions::to_decimal(rhs_oid);
            if (rhs == 0) {
                return ObjectId::get_null();
            }
            auto lhs = GQL::Conversions::to_decimal(lhs_oid);
            return GQL::Conversions::pack_decimal(lhs / rhs);
        }
        case GQL::Conversions::OPTYPE_DECIMAL: {
            auto rhs = GQL::Conversions::to_decimal(rhs_oid);
            if (rhs == 0) {
                return ObjectId::get_null();
            }
            auto lhs = GQL::Conversions::to_decimal(lhs_oid);
            return GQL::Conversions::pack_decimal(lhs / rhs);
        }
        case GQL::Conversions::OPTYPE_FLOAT: {
            auto lhs = GQL::Conversions::to_float(lhs_oid);
            auto rhs = GQL::Conversions::to_float(rhs_oid);
            // Division by zero, etc is handle by the floating point implementation.
            // SPARQL 1.1 follows IEEE 754-2008.
            return GQL::Conversions::pack_float(lhs / rhs);
        }
        case GQL::Conversions::OPTYPE_DOUBLE: {
            auto lhs = GQL::Conversions::to_double(lhs_oid);
            auto rhs = GQL::Conversions::to_double(rhs_oid);
            // Division by zero, etc is handle by the floating point implementation.
            // SPARQL 1.1 follows IEEE 754-2008.
            return GQL::Conversions::pack_double(lhs / rhs);
        }
        case GQL::Conversions::OPTYPE_INVALID: {
            return ObjectId::get_null();
        }
        default:
            throw LogicException("This should never happen");
        }
    }

    void accept_visitor(BindingExprVisitor& visitor) override
    {
        visitor.visit(*this);
    }
};
} // namespace GQL
