#pragma once

#include <memory>

#include "query/parser/expr/expr.h"

namespace SPARQL {
class ExprAggCountAll : public Expr {
public:
    bool distinct;

    ExprAggCountAll(bool distinct) :
        distinct (distinct) { }

    virtual std::unique_ptr<Expr> clone() const override {
        return std::make_unique<ExprAggCountAll>(distinct);
    }

    void accept_visitor(ExprVisitor& visitor) override {
        visitor.visit(*this);
    }

    std::set<VarId> get_all_vars() const override {
        return {};
    }

    bool has_aggregation() const override {
        return true;
    }

    virtual std::ostream& print_to_ostream(std::ostream& os, int indent = 0) const override {
        return os << std::string(indent, ' ') << "COUNT(" << (distinct ? "DISTINCT " : "") << "*)";
    }
};
} // namespace SPARQL
