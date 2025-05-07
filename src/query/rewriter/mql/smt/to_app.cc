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
                std::vector<std::unique_ptr<Expr>> param;
                for (auto& ele: app ->param_list){
                    if (is_cast_to<SMT::ExprApp>(ele.get()))
                    {
                        auto child = dynamic_cast< ExprApp*>(ele.get());
                        if (child -> op == Operator::Add)
                        {
                            for (auto& children_child: child ->param_list){
                                flattening_smt_expr(children_child.get());
                                param.push_back(child->clone());
                            }
                        } else {
                            {
                                param.push_back(ele ->clone());
                            }
                        }
                    } else {
                        param.push_back(ele ->clone());
                    }

              }
                app ->param_list = std::move(param);
                break;
          }
            case Operator::Mul: {
                std::vector<std::unique_ptr<Expr>> param;
                for (auto& ele: app ->param_list){
                    if (is_cast_to<SMT::ExprApp>(ele.get()))
                    {
                        auto child = dynamic_cast< ExprApp*>(ele.get());
                        if (child -> op == Operator::Mul)
                        {
                            for (auto&& children_child: child ->param_list){
                                flattening_smt_expr(children_child.get());
                                param.push_back(children_child->clone());
                            }
                        } else {
                            {
                                param.push_back(child->clone());
                            }
                        }
                    }else {
                        param.push_back(ele ->clone());
                    }

                }
                app ->param_list = std::move(param);
                break;

        }
        case Operator::Eq: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
                break;

                }


        case Operator::Gte: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
                break;

            }
        case Operator::Lte: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
                break;

            }
        case Operator::Neq: {
                for (auto& ele: app ->param_list) {
                    flattening_smt_expr(ele.get());
                }
                break;

            }
        case Operator::And: {
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
