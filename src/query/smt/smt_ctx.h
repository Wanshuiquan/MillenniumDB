//
// Created by lhy on 11/11/24.
//

#ifndef MILLENNIUMDB_SMT_CTX_H
#define MILLENNIUMDB_SMT_CTX_H
#pragma once
#include <variant>
#include <map>
#include <sstream>
#include <iostream>
#include <fstream>
#include <chrono>
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

    // storage z3 expressions
    z3::ast_vector_tpl<z3::expr> expr_vec = z3::ast_vector_tpl<z3::expr>(context);
    std::map<std::string, int> expr_map;
    int index_expr = 0;

    // store z3 terms
    z3::ast_vector_tpl<z3::expr> terms = z3::ast_vector_tpl<z3::expr>(context);
    std::map<int64_t, int> term_index_map;
    int index_term = 0;

    // operation time statistics
    long long other_total_time_ns = 0;
    long long solver_total_time_ns = 0;

    template<typename Func>
    auto time_operation(Func&& func, long long& total_time_ns ) {
        auto start = std::chrono::steady_clock::now();
        auto result = func();
        auto end = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

        total_time_ns += duration.count();
        return result;
    }
    template<typename Func>
    auto time_operation_void(Func&& func, long long& total_time_ns) {
        auto start = std::chrono::steady_clock::now();
        func();
        auto end = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

        total_time_ns += duration.count();
    }
    z3::solver solver = z3::solver(context);

public:

    SMTContext(){
        dels.push_back(epsilon.decl());
    }

   
    long long get_solver_run_time(){
        return solver_total_time_ns;
    }

    long long get_other_run_time(){
        return other_total_time_ns;
    }
    
    void set_solver_time(long long time_ns){
        solver_total_time_ns = time_ns;
    }
     
    void set_operation_time(long long time_ns){
        other_total_time_ns = time_ns;
    }
    z3::context* get_context() {
       return time_operation(
                [&]() {
                    return &context;
                }, other_total_time_ns);
    }
    void add_bool_var(const std::string& name){
        time_operation_void(
                [&]() {
                    auto var = context.bool_const(name.c_str());
                    if (vars.find(name) == vars.end()) {
                        dels.push_back(var.decl());
                        var_vec.push_back(var);

                        vars.emplace(name, index);
                        index = index + 1;
                    }
                }, other_total_time_ns);
    }
    z3::expr add_bool_val(bool val) {
        return time_operation(
                [&]() {
                    return context.bool_val(val);
                }, other_total_time_ns);
    }
    void add_real_var(const std::string& name) {
        time_operation_void(
                [&]() {
                    auto var = context.real_const(name.c_str());
                    if (vars.find(name) == vars.end()) {
                        dels.push_back(var.decl());
                        var_vec.push_back(var);

                        vars.emplace(name, index);
                        index = index + 1;
                    }
                }, other_total_time_ns);
    }

    z3::expr add_real_val(double val) {
        return  time_operation(
                [&]() {
                    return context.real_val(std::to_string(val).c_str());
                }, other_total_time_ns);
    }

    void add_string_var(const std::string& name) {
        time_operation_void(
                [&]() {
                    auto var = context.string_const(name.c_str());
                    if (vars.find(name) == vars.end()) {
                        dels.push_back(var.decl());
                        var_vec.push_back(var);

                        vars.emplace(name, index);
                        index = index + 1;
                    }
                }, other_total_time_ns);
    }
    z3::expr add_string_val(const std::string& val) {
        return time_operation(
                [&]() {
                    return context.string_val(val.c_str());
                }, other_total_time_ns);
    }

    void add_obj_var(const std::string&  name) {
        time_operation_void(
                [&]() {
                    dels.push_back(context.function(name.c_str(), 0, 0, REAL));
                }, other_total_time_ns);
    }

    z3::expr add_obj_val(uint64_t val) {
        return   time_operation(
                [&]() {
                    return context.real_val(val);
                }, other_total_time_ns);
    }

    z3::expr parse (const std::string& formula) {
        return   time_operation(
                [&]() {
                    auto res = expr_map.find(formula);
                    if (res == expr_map.end()) {
                        auto f = context.parse_string(formula.c_str(), sort, dels)[0];
                        expr_vec.push_back(f);
                        expr_map[formula] = index_expr;
                        index_expr = index_expr + 1;
                        return f;
                    } else {
                        auto id = expr_map[formula];
                        return expr_vec[id];
                    }
                }, other_total_time_ns);
    }

    z3::ast_vector_tpl<z3::expr> decompose(const z3::expr& f) {
        return   time_operation(
                [&]() {
                    if (f.is_and()) {
                        auto res = f.args();
                        return res;
                    } else {
                        auto vec = z3::ast_vector_tpl<z3::expr>(context);
                        vec.push_back(f);
                        return vec;
                    }
                }, other_total_time_ns);
    }
    z3::expr subsitute_obj(const std::string& name, uint64_t val, const z3::expr& formula) {
        return  time_operation(
                [&]() {
                    Z3_ast var[] = {context.real_const(name.c_str())};
                    Z3_ast value[] = {context.real_val(val)};

                    z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value));
                    return novi_expr;
                }, other_total_time_ns);
    }

    z3::expr subsitute_real(const std::string& name, double val, const z3::expr& formula) {
        return time_operation(
                [&]() {
                    int ind = vars[name];
                    auto v = var_vec[ind];
                    Z3_ast var[] = {v};
                    Z3_ast value[] = {context.real_val(std::to_string(val).c_str())};
                    z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value));
                    return novi_expr;
                }, other_total_time_ns);
    }
    z3::expr subsitute_bool(const std::string& name, bool val, const z3::expr& formula) {
        return   time_operation(
                [&]() {
                    int ind = vars[name];
                    auto v = var_vec[ind];
                    Z3_ast var[] = {v};
                    Z3_ast value[] = {context.bool_val(std::to_string(val).c_str())};
                    z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value));
                    return novi_expr;
                }, other_total_time_ns);
    }
    z3::expr subsitute_string(const std::string& name, const std::string& val, const z3::expr& formula) {
        return  time_operation(
                [&]() {
                    int ind = vars[name];
                    auto v = var_vec[ind];
                    Z3_ast var[] = {v};
                    Z3_ast value[] = {context.string_val(val)};
                    z3::expr novi_expr = z3::to_expr(context, Z3_substitute(context, formula, 1, var, value));
                    return novi_expr;
                }, other_total_time_ns);
    }

    z3::expr normalizition(const z3::expr& formula) {
        return   time_operation(
                [&]() {
                    z3::params params(context);
                    params.set("arith_lhs", true);
                    params.set("arith_ineq_lhs", true);
                    z3::tactic t = z3::with(z3::tactic(context, "simplify"), params);
                    z3::goal g(context);
                    g.add(formula);
                    auto res = t(g);
                    z3::goal subgoal = res[0];
                    return subgoal.as_expr().simplify();
                }, other_total_time_ns);
    }
    z3::expr get_term(int64_t id) {
        return   time_operation(
                [&]() {
                    auto term_index = term_index_map[id];
                    return terms[term_index];
                }, other_total_time_ns);
    }
    // return the key of the ast and add the ast to vector if not exists
    int64_t add_a_term(const z3::expr& formula) {
        return    time_operation(
                [&]() {
                    auto id = Z3_get_ast_id(context, formula.operator Z3_ast());
                    if (term_index_map.find(id) == term_index_map.end()) {
                        terms.push_back(formula);
                        term_index_map[id] = index_term;
                        index_term = index_term + 1;
                    }
                    return id;
                }, other_total_time_ns);
    }



    std::tuple<Bound, int64_t, z3::expr> get_bound(const z3::expr& formula) {
        return  time_operation(
                [&]() {
                    if (formula.is_app()) {
                        z3::expr lhs = formula.arg(0);
                        auto lhs_id = add_a_term(lhs);
                        z3::expr rhs = formula.arg(1);
                        switch (formula.decl().decl_kind()) {
                            case Z3_OP_EQ:
                                return  std::tuple<Bound, int64_t, z3::expr>{Bound::EQ, lhs_id, rhs};
                            case Z3_OP_GE:
                                return  std::tuple<Bound, int64_t, z3::expr>{Bound::Ge, lhs_id, rhs};
                            case Z3_OP_LE:
                                return  std::tuple<Bound, int64_t, z3::expr>{Bound::Le, lhs_id, rhs};
                            default:
                                throw std::logic_error("Not support");
                        }
                    } else {
                        throw std::logic_error("Should be app formulas");
                    }
                }, other_total_time_ns);
    }

    void print_bound(std::tuple<Bound, z3::expr, z3::expr> bound, std::ostream& os) {
        time_operation_void(
                [&]() {
                    auto lhs = std::get<1>(bound);
                    auto rhs = std::get<2>(bound);
                    switch (std::get<0>(bound)) {
                        case Bound::EQ:
                            os << "EQ" << " " << lhs << " " << rhs << std::endl;
                            break;
                        case Bound::Le:
                            os << "Le" << " " << lhs << " " << rhs << std::endl;
                            break;
                        case Bound::Ge:
                            os << "Ge" << " " << lhs << " " << rhs << std::endl;
                            break;
                    }
                }, other_total_time_ns);
    }

    z3::expr get_var(const std::string & name) {
        return  time_operation(
                [&]() {
                    int ind = vars[name];
                    return var_vec[ind];
                }, other_total_time_ns);
    }
    //function for solver operation
    z3::solver get_solver(){
        return  time_operation(
                [&]() {
                    return solver;
                }, solver_total_time_ns);
    }

    auto check(z3::solver& s) {
        return time_operation([&]() {
            return s.check();
        },solver_total_time_ns);
    }

    auto get_model(z3::solver& s) {
        return time_operation([&]() {
            return s.get_model();
        },solver_total_time_ns);
    }

    void solver_add_epsilon_condition(z3::solver&s){
        time_operation_void(
                [&]() {
                  s.add(bound_epsilon);
                },solver_total_time_ns);
    }
    void solver_add_condition(z3::solver&s, z3::expr f){
        time_operation_void(
                [&]() {
                    s.add(f);
                },solver_total_time_ns);
    }
    void solver_push(z3::solver&s){
        time_operation_void(
                [&]() {
                    s.push();
                },solver_total_time_ns);
    }
    void solver_pop(z3::solver&s){
        time_operation_void(
                [&]() {
                    s.pop();
                },solver_total_time_ns);
    }
    void solver_reset(z3::solver&s){
        time_operation_void(
                [&]() {
                    s.reset();
                },solver_total_time_ns);
    }
};

class SMTCtx {
private:
    static inline thread_local std::unique_ptr<SMTContext> ctx = std::make_unique<SMTContext>();
public:
    static void reset(){
        ctx = std::make_unique<SMTContext>();
    }

    static SMTContext& get_ctx(){
        return  *ctx;
    }
};





inline SMTContext& get_smt_ctx(){
    return SMTCtx::get_ctx();
}

inline void reset_smt(){
    SMTCtx::reset();
}
#endif //MILLENNIUMDB_SMT_CTX_H
