//
// Created by heyang-li on 4/22/25.
//

#include "ir.h"
#include "boost/format.hpp"
#include <iostream>
#include <sstream>

std::string LinearInequality::to_smt_lib(){
        std::stringstream lhs_param_formula;
        bool lhs_param_true = false;
        for (const auto &key: lhs_param){
            lhs_param_formula << boost::format("(* %1 %2)")%key.first%key.second;
            lhs_param_true = true;
        }


        std::stringstream  lhs_attr_formula;
        bool lhs_attr_true = false;
        for (const auto & key: lhs_attr){
            lhs_param_formula << boost::format("(* %1 %2)")%key.first%key.second;
            lhs_attr_true = true;
        }

        double lhs_cons = std::accumulate(lhs_constant.begin(), lhs_constant.end(), 0.0);

    }



void LinearInequality::build_inequality_map(SMT::Expr &) {


}