//
// Created by lhy on 8/20/24.
//
#pragma  once

#ifndef MILLENNIUMDB_REWRITE_TO_SMT_H
#define MILLENNIUMDB_REWRITE_TO_SMT_H
#include <cassert>
#include <memory>
#include "query/parser/op/op_visitor.h"
#include "query/parser/op/sparql/ops.h"
#include "rewrite_rule.h"
#include "query/parser/paths/path_atom.h"
#include "query/parser/paths/path_smt_atom.h"
namespace SPARQL{
    class ToSMT: RewriteRule{
        bool is_possible_to_regroup(std::unique_ptr<Expr>& unknown_expr) override{
            return is_castable_to<PathAtom>(unknown_expr);
        }

        std::unique_ptr<Expr> regroup(std::unique_ptr<Expr> unknown_expr) override{
            auto top = std::vector<std::shared_ptr<Expr>>();
            auto path_atom = cast_to<PathAtom>(std::move(unknown_expr));
            top.push_back(std::make_shared<ExprObjectId>(ObjectId(ObjectId::BOOL_TRUE)));
            return std::make_unique<SMTAtom>(path_atom->atom, path_atom->inverse, std::move(top));

        }
    };
class RewriteToSMT: public RewriteRule{
private:
    ExprRewriteRuleVisitor expr_visitor;
public:
    bool is_possible_to_regroup(std::unique_ptr<Op>& unknown_op) override{
        if (!is_castable_to<OpPath>(unknown_op)){
            return false;
        }
        else{
            std::unique_ptr<OpPath> path_expr = cast_to<OpPath>(std::move(unknown_op));
            if (path_expr->semantic == PathSemantic::DATA_TEST){

            }
        }
    }


    std::unique_ptr<Op> regroup(std::unique_ptr<Op> unknown_op) override {
        return unknown_op;
    }


};
}
#endif //MILLENNIUMDB_REWRITE_TO_SMT_H
