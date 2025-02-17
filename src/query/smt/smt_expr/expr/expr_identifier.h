//
// Created by heli on 8/25/24.
//
#include "query/query_context.h"
#include "query/smt/smt_expr/smt_expr.h"
#ifndef EXPR_IDENTIFIER_H
#define EXPR_IDENTIFIER_H
namespace SMT {
    class ExprAttr : public Expr {
    public:
        ObjectId var;
        std::string name; 

        ExprAttr(ObjectId var, std::string name) :
            var (var), name(name) { }
        ExprAttr(ExprAttr& expr) :var(expr.var), name(expr.name) { }

        std::unique_ptr<Expr> clone() const override {
            return std::make_unique<ExprAttr>(var, name);
        }

        void accept_visitor(ExprVisitor& visitor) override {
            visitor.visit(*this);
        }

        bool has_aggregation() const override { return false; }
        
        std::string to_smt_lib() const{
            return name;
        }
        std::set<VarId> get_all_vars() const override {
            return { };
        }
        
        std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const override {
        return std::set<std::tuple<std::string, ObjectId>>({{name, var}});
    }
         std::set<VarId> get_all_parameter() const override {
            return {}; 
         }
    };
}
#endif //EXPR_IDENTIFIER_H
