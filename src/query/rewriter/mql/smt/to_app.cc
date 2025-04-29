//
// Created by heyang-li on 4/23/25.
//

#include "to_app.h"
using namespace SMT;

void ToAPP::flattening_smt_expr(Expr* expr)
{
    if (is_cast_to<SMT::ExprApp>(expr))
    {
        auto app = dynamic_cast<ExprApp*>(expr);
        switch (app -> op) {
            case Operator::Add: {
                for (auto& ele: app ->param_list){
                    flattening_smt_expr(ele.get());
                    if (is_cast_to<SMT::ExprApp>(ele.get()))
                    {
                        auto ele_app = dynamic_cast< ExprApp*>(ele.get());
                        if (ele_app -> op == Operator::Add)
                        {
                            for (auto&& ele_ele: ele_app ->param_list){
                                app->param_list.push_back(ele_ele->clone());
                            }
                        }
                    }
              }
          }
            case Operator::Mul: {
                    for (auto& ele: app ->param_list){
                        flattening_smt_expr(ele.get());
                        if (is_cast_to<SMT::ExprApp>(ele.get()))
                        {
                            auto ele_app = dynamic_cast< ExprApp*>(ele.get());
                            if (ele_app -> op == Operator::Mul)
                            {
                                for (auto&& ele_ele: ele_app ->param_list){
                                    app->param_list.push_back(ele_ele->clone());
                                }
                            }
                        }
                    }
        }
        case Operator::Eq: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
                }


        case Operator::Gte: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
            }
        case Operator::Lte: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
            }
        case Operator::Neq: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
            }
        default:
            return;

    }
}
}

int ToAPP::rank(Expr* expr, int init)
{
    if (is_cast_to<SMT::ExprApp>(expr))
    {
        auto app = dynamic_cast<ExprApp*>(expr);
        std::vector<int> res;
        for (auto& ele: app ->param_list){
            res.push_back(rank(ele.get(), init + 1));
            return *std::max_element(res.begin(), res.end());
        }
    }
    return init;
}
