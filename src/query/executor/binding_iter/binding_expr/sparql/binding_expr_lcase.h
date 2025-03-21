#pragma once

#include <memory>
#include <string>

#include "misc/transliterator.h"
#include "graph_models/rdf_model/conversions.h"
#include "query/executor/binding_iter/binding_expr/binding_expr.h"

namespace SPARQL {
class BindingExprLCase : public BindingExpr {
private:
    static std::string lcase(const std::string& str) {
        return Transliterator::get_instance()->lowercase(str);
    }

public:
    std::unique_ptr<BindingExpr> expr;

    BindingExprLCase(std::unique_ptr<BindingExpr> expr) :
        expr (std::move(expr)) { }

    ObjectId eval(const Binding& binding) override {
        auto expr_oid = expr->eval(binding);

        switch (RDF_OID::get_generic_sub_type(expr_oid)) {
        case RDF_OID::GenericSubType::STRING_SIMPLE: {
            std::string str = Conversions::unpack_string(expr_oid);
            return Conversions::pack_string_simple(lcase(str));
        }
        case RDF_OID::GenericSubType::STRING_XSD: {
            std::string str = Conversions::unpack_string(expr_oid);
            return Conversions::pack_string_xsd(lcase(str));
        }
        case RDF_OID::GenericSubType::STRING_LANG: {
            auto&& [lang, str] = Conversions::unpack_string_lang(expr_oid);
            return Conversions::pack_string_lang(lang, lcase(str));
        }
        default:
            return ObjectId::get_null();
        }
    }

    void accept_visitor(BindingExprVisitor& visitor) override {
        visitor.visit(*this);
    }
};
} // namespace SPARQL
