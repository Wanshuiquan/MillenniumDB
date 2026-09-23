#pragma once
#include <stdexcept>
#include <string>
#include <unordered_map>
#include "z3++.h"
#include "query/smt/fixed_numeric_policy.h"
namespace SMT::Real {
template <typename NumericPolicy>
class FloatingPointRewriter {
public: 
    static z3::expr rewrite(const z3::expr& e,std::unordered_map<std::string,z3::expr>& v)
        {return e.is_bool()?boolean(e,v):term(e,v);}
private:
 static z3::expr numeral_to_fp(const z3::expr& e)
        {
            auto& c=e.ctx();
            auto fp_sort = c.fpa_sort(
                    NumericPolicy::floating_point_exponent_bits,
                    NumericPolicy::floating_point_significand_bits);
            z3::expr real_expr = e.is_real() ? e : z3::to_real(e);
            return z3::to_expr(c, Z3_mk_fpa_to_fp_real(c, c.fpa_rounding_mode(), real_expr, fp_sort)).simplify();
        }
 static z3::expr variable(const std::string& n,z3::context& c,std::unordered_map<std::string,z3::expr>& v)
        {
            auto it=v.find(n);
            if(it!=v.end()) return it->second;
             return v.emplace(
                     n,
                     c.fpa_const(
                             n.c_str(),
                             NumericPolicy::floating_point_exponent_bits,
                             NumericPolicy::floating_point_significand_bits)).first->second;
            }
 static z3::expr term(const z3::expr& e,std::unordered_map<std::string,z3::expr>& v)
        {
            auto& c=e.ctx();
            if(e.is_numeral()) return numeral_to_fp(e);
            if(e.is_const()) return variable(e.to_string(),c,v);
            const auto k=e.decl().decl_kind();
            if(k==Z3_OP_ITE) return z3::ite(boolean(e.arg(0),v),term(e.arg(1),v),term(e.arg(2),v));
            if(k==Z3_OP_UMINUS) return -term(e.arg(0),v);
            if(k==Z3_OP_TO_REAL) return term(e.arg(0),v);
            if (k == Z3_OP_ADD || k == Z3_OP_SUB || k == Z3_OP_MUL || k == Z3_OP_DIV) {
                auto r=term(e.arg(0),v);
                for(unsigned i=1;i<e.num_args();++i){
                    auto x=term(e.arg(i),v);
                    if(k==Z3_OP_ADD) r=r+x;
                    else if(k==Z3_OP_SUB) r=r-x;
                    else if(k==Z3_OP_MUL) r=r*x;
                    else r=r/x;
                }
                return r;
            }
            throw std::invalid_argument("unsupported real term in floating-point rewrite");
        }
 static z3::expr boolean(const z3::expr& e,std::unordered_map<std::string,z3::expr>& v)
        {
            auto& c=e.ctx();
            if(e.is_true()||e.is_false()) return c.bool_val(e.is_true());
            const auto k=e.decl().decl_kind();
            if(k==Z3_OP_NOT) return!boolean(e.arg(0),v);
            if(k==Z3_OP_IMPLIES) return z3::implies(boolean(e.arg(0),v), boolean(e.arg(1),v));
            if(k==Z3_OP_ITE) return z3::ite(boolean(e.arg(0),v), boolean(e.arg(1),v), boolean(e.arg(2),v));
            if(k==Z3_OP_AND||k==Z3_OP_OR){
                auto r=boolean(e.arg(0),v);
                for(unsigned i=1;i<e.num_args();++i) {
                    r=k==Z3_OP_AND?r&&boolean(e.arg(i),v) :r||boolean(e.arg(i),v);
                }
                return r;
            }
            auto l=term(e.arg(0),v),r=term(e.arg(1),v);
            if(k==Z3_OP_EQ) return z3::fp_eq(l,r);
            if(k==Z3_OP_DISTINCT)return!z3::fp_eq(l,r);
            if(k==Z3_OP_LE) return l<=r;
            if(k==Z3_OP_LT)return l<r;
            if(k==Z3_OP_GE)return l>=r;
            if(k==Z3_OP_GT)return l>r;
            throw std::invalid_argument("unsupported Boolean term in floating-point rewrite");}
};

using FloatingPointRewriter64 = FloatingPointRewriter<SMT::FixedInt64Binary64Policy>;
} // namespace SMT::Real
