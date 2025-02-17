//
// Created by heli on 8/23/24.
//
#pragma once

#include <set>
#include <memory>
#include <ostream>

#include "query/var_id.h"
#include "graph_models/object_id.h"
#include "query/smt/smt_expr/smt_expr_visitor.h"

namespace SMT {
class Expr {
public:
    virtual ~Expr() = default;
    Expr& operator=(const Expr&)  = default;
    virtual std::unique_ptr<Expr> clone() const = 0;

    virtual void accept_visitor(ExprVisitor&) = 0;
    std::string to_string() const {return to_smt_lib();}
    virtual std::set<VarId> get_all_vars() const = 0;
    virtual std::string to_smt_lib()  const =  0; 
    virtual std::set<std::tuple<std::string, ObjectId>> get_all_attrs() const = 0;
    virtual std::set<VarId> get_all_parameter() const = 0;

    virtual bool has_aggregation() const = 0;
};
}