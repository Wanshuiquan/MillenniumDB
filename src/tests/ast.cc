//
// Created by lhy on 8/5/24.
//
#include "query/parser/sparql_query_parser.h"
#include "query/parser/grammar/error_listener.h"
#include "query/query_context.h"


#include <iostream>
#include <string>
#include<vector>
#include "z3++.h"

std::string query =  "PREFIX : <http://www.path.com/> \n PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \n \nSELECT * \n WHERE {\n?s xsd:q1/a+ ?o. \n}";
int verify_z3_expression(){
    std::cout << "de-Morgan example\n";

    z3::context c;

    z3::expr x = c.bool_const("x");
    z3::expr y = c.bool_const("y");
    z3::expr conjecture = (!(x && y)) == (!x || !y);

    z3::solver s(c);
    // adding the negation of the conjecture as a constraint.
    s.add(!conjecture);
    std::cout << s << "\n";
    std::cout << s.to_smt2() << "\n";
    switch (s.check()) {
        case z3::unsat:   std::cout << "de-Morgan is valid\n"; break;
        case z3::sat:     std::cout << "de-Morgan is not valid\n"; break;
        case z3::unknown: std::cout << "unknown\n"; break;
    }
    return 0;
}

int try_parser(){
    QueryContext::set_query_ctx(new QueryContext());
    antlr4::MyErrorListener error_listener;
    auto plan = SPARQL::QueryParser::get_query_plan(query, &error_listener);
    std::cout<<*plan<< std::endl;
    return 0;
}

int main(){
    try_parser();
    return 0;
}