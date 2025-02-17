//
// Created by lhy on 11/11/24.
//

#ifndef MILLENNIUMDB_SMT_CTX_H
#define MILLENNIUMDB_SMT_CTX_H
#pragma once
#include <variant>
#include <iostream>
#include <map>


#include "z3++.h"
enum Ty{
    Str,
    Real
};
enum Bound {
    Ge,
    Le,
    EQ,
};


class SMTContext{
public:

    z3::context context = z3::context();
    // The definition of Sorts
    z3::sort_vector sort = z3::sort_vector(context);
    z3::sort STRING = context.string_sort();
    z3::sort REAL = context.real_sort();
    z3::sort BOOL = context.bool_sort();
    // the definition of epsilon
    z3::expr epsilon = context.real_const("epsilon");
    z3::expr bound_epsilon = epsilon > 0;
    //The definition of func vector
    z3::func_decl_vector dels = z3::func_decl_vector(context);

    //store vars
    z3::ast_vector_tpl<z3::expr> var_vec = z3::ast_vector_tpl<z3::expr>(context);
    std::map<std::string, int> vars;
    std::map<std::string, Ty> type;

    int index = 0;

    // storage exprs
    z3::ast_vector_tpl<z3::expr> expr_vec = z3::ast_vector_tpl<z3::expr>(context);
    std::map<std::string, int> expr_map;
    int index_expr = 0;
    SMTContext(){
        dels.push_back(epsilon.decl());
    }
    void add_bool_var(const std::string& name){
        dels.push_back(context.function(name.c_str(),0,0,BOOL));
    }
    z3::expr add_bool_val(bool val) {
        return context.bool_val(val);

    }
    void add_real_var(const std::string& name) {
        auto var = context.real_const(name.c_str());
        if (vars.find(name) == vars.end()) {
            dels.push_back(var.decl());
            var_vec.push_back(var);

            vars.emplace(name, index);
            index = index + 1;
        }
    }
    z3::expr add_real_val(double val){
        return context.real_val(std::to_string(val).c_str());
    }

    void add_string_var(const std::string& name){
        auto var = context.string_const(name.c_str());
        if (vars.find(name) == vars.end()) {
            dels.push_back(var.decl());
            var_vec.push_back(var);

            vars.emplace(name, index);
            index = index + 1;
        }
    }
    z3::expr add_string_val(const std::string& val){
        return context.string_val(val.c_str());
    }

    void add_obj_var(const std::string&  name){
        dels.push_back(context.function(name.c_str(),0,0,REAL));
    }

    z3::expr add_obj_val(uint64_t val){
        return context.real_val(val);
    }

    z3::expr parse (const std::string& formula){
        auto res = expr_map.find(formula);
        if (res == expr_map.end()){
            auto f = context.parse_string(formula.c_str(), sort, dels)[0];
            expr_vec.push_back(f);
            expr_map[formula] = index_expr;
            index_expr = index_expr + 1;
            return f;
        }else{
            auto id = expr_map[formula];
            return expr_vec[id];
        }

    }

    z3::ast_vector_tpl<z3::expr> decompose(const z3::expr& f){
        if (f.is_and()) {
            auto res = f.args();
            return res;
        }
        else {
            auto vec = z3::ast_vector_tpl<z3::expr>(context);
            vec.push_back(f);
            return vec;
        }
    }
    z3::expr subsitute_obj(const std::string& name, uint64_t val, const z3::expr& formula){
        Z3_ast var[] = {context.real_const(name.c_str())};
        Z3_ast value[] = {context.real_val(val)};

        z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value ));
        return novi_expr;
    }

    z3::expr subsitute_real(const std::string& name, double val, const z3::expr& formula){
        int ind = vars[name];
        auto v = var_vec[ind];
        Z3_ast var[] = {v};
        Z3_ast value[] = {context.real_val(std::to_string(val).c_str())};
        z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value ));
        return novi_expr;
    }

    z3::expr subsitute_string(const std::string& name, const std::string& val, const z3::expr& formula){
        int ind = vars[name];
        auto v = var_vec[ind];
        Z3_ast var[] = {v};
        Z3_ast value[] = {context.string_val(val)};
        z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value ));
        return novi_expr;
    }

    z3::expr normalizition(const z3::expr& formula) {
        z3::params params(context);
        params.set("arith_lhs", true);
        params.set("arith_ineq_lhs", true);
        z3::tactic t = z3::with(z3::tactic(context, "simplify"),params);
        z3::goal g(context);
        g.add(formula);
        auto res = t(g);
        z3::goal subgoal = res[0];
        return subgoal.as_expr().simplify();
    }

    std::tuple<Bound, z3::expr, z3::expr> get_bound(const z3::expr& formula){
        if (formula.is_app()){
            z3::expr lhs = formula.arg(0);
            z3::expr rhs = formula.arg(1);
            switch (formula.decl().decl_kind()) {
                case Z3_OP_EQ: return {Bound::EQ, lhs, rhs};
                case Z3_OP_GE: return {Bound::Ge, lhs, rhs};
                case Z3_OP_LE: return {Bound::Le, lhs, rhs};
                default: throw std::logic_error("Not support");
            }
        }
        else{
            throw std::logic_error("Should be app formulas");
        }
    }

    void print_bound(std::tuple<Bound, z3::expr, z3::expr> bound, std::ostream& os){
        auto lhs = std::get<1>(bound);
        auto rhs = std::get<2>(bound);
        switch (std::get<0>(bound)) {
            case Bound::EQ: os<< "EQ" <<" " << lhs <<  " "<< rhs << std::endl; break;
            case Bound::Le: os << "Le" << " " << lhs << " " << rhs << std::endl; break;
            case Bound::Ge: os << "Ge" << " " << lhs << " "<< rhs << std::endl; break;
        }
    }

    z3::expr get_var(const std::string & name){
        int ind = vars[name];
        return var_vec[ind];
    }



};

class SMTCtx {
private:
    SMTContext* ctx = new SMTContext();
public:
    void reset(){
        auto temp = ctx;
        ctx = new SMTContext();
        delete temp;
    }

    SMTContext& get_ctx(){
        return  *ctx;
    }
};


inline SMTCtx* ctx = new SMTCtx();


inline SMTContext& get_smt_ctx(){
    return ctx->get_ctx();
}

inline void reset_smt(){
    ctx -> reset();
}
#endif //MILLENNIUMDB_SMT_CTX_H
