#pragma once

#include <memory>

#include "graph_models/rdf_model/conversions.h"
#include "query/executor/binding_iter/binding_expr/binding_expr.h"

namespace SPARQL {
class BindingExprStrLang : public BindingExpr {
public:
    std::unique_ptr<BindingExpr> expr1;
    std::unique_ptr<BindingExpr> expr2;

    BindingExprStrLang(std::unique_ptr<BindingExpr> expr1,
                       std::unique_ptr<BindingExpr> expr2) :
        expr1 (std::move(expr1)),
        expr2 (std::move(expr2)) { }

    ObjectId eval(const Binding& binding) override {
        auto expr1_oid = expr1->eval(binding);
        auto expr2_oid = expr2->eval(binding);

        auto expr1_subtype = RDF_OID::get_generic_sub_type(expr1_oid);
        if (expr1_subtype != RDF_OID::GenericSubType::STRING_SIMPLE &&
            expr1_subtype != RDF_OID::GenericSubType::STRING_XSD)
        {
            return ObjectId::get_null();
        }

        auto expr2_subtype = RDF_OID::get_generic_sub_type(expr2_oid);
        if (expr2_subtype != RDF_OID::GenericSubType::STRING_SIMPLE)
        {
            return ObjectId::get_null();
        }

        auto str = Conversions::to_lexical_str(expr1_oid);
        auto lang = Conversions::unpack_string(expr2_oid);
        return Conversions::pack_string_lang(lang, str);
    }

    void accept_visitor(BindingExprVisitor& visitor) override {
        visitor.visit(*this);
    }
};
} // namespace SPARQL
