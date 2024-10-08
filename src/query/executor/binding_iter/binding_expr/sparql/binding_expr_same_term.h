#pragma once

#include <memory>

#include "graph_models/object_id.h"
#include "query/executor/binding_iter/binding_expr/binding_expr.h"

namespace SPARQL {
class BindingExprSameTerm : public BindingExpr {
public:
    std::unique_ptr<BindingExpr> lhs;
    std::unique_ptr<BindingExpr> rhs;

    BindingExprSameTerm(std::unique_ptr<BindingExpr> lhs, std::unique_ptr<BindingExpr> rhs) :
        lhs(std::move(lhs)), rhs(std::move(rhs)) { }

    ObjectId eval(const Binding& binding) override {
        auto lhs_oid = lhs->eval(binding);
        auto rhs_oid = rhs->eval(binding);

        // Unlike RDFterm-equal (=), sameTerm can be used to test for
        // non-equivalent typed literals with unsupported datatypes.
        if (lhs_oid.is_null() || rhs_oid.is_null()) {
            // Nulls are not equal to anything, including other nulls.
            return ObjectId::get_null();
        } else {
            return ObjectId(ObjectId::MASK_BOOL | (lhs_oid == rhs_oid));
        }
    }

    std::ostream& print_to_ostream(std::ostream& os) const override {
        os << "sameTERM(" << *lhs << ", " << *rhs << ")";
        return os;
    }
};
} // namespace SPARQL
