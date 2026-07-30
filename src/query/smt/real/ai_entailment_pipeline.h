#pragma once
#include <unordered_map>
#include <vector>
#include "query/smt/real/entailment_pipeline.h"
#include "query/smt/real/floating_point_rewriter.h"
#include "query/smt/real/nra_abstract_domain.h"
namespace SMT::Real {
class AIEntailmentPipeline {
public: 

AtomDecision evaluate_and_update(std::vector<z3::expr>& fp,std::vector<z3::expr>& exact,const z3::expr& atom)
        {
            if(atom.is_true()) return AtomDecision::Redundant;
            if(atom.is_false()) return AtomDecision::Inconsistent;
            const bool atom_fits = is_abstractable(atom)
                                   && NRAAbstractDomain::fits_binary64(NRAAbstractDomain::infer(atom));
            const bool full_abstract_cover = atom_fits && fp.size() == exact.size();
            if(!full_abstract_cover)
            return exact_.evaluate_and_update(fp,exact,atom);
            auto f=FloatingPointRewriter64::rewrite(atom,vars_);
            if(is_sat_with_extra(fp,!f)) {
                if(is_sat_with_extra(fp,f)) {
                    fp.push_back(f);exact.push_back(atom);
                    return AtomDecision::Keep;
                }
                if(is_sat_with_extra(exact,atom)) {
                    fp.push_back(f);exact.push_back(atom);
                    return AtomDecision::Keep;
                }
                return AtomDecision::Inconsistent;
            }
            if(!is_sat_with_extra(exact,!atom)) return AtomDecision::Redundant;
            if(is_sat_with_extra(fp,f)) {
                fp.push_back(f);exact.push_back(atom);
                return AtomDecision::Keep;
            }
            if(is_sat_with_extra(exact,atom)) {
                fp.push_back(f);exact.push_back(atom);
                return AtomDecision::Keep;
            }
            return AtomDecision::Inconsistent;
        }

    bool check_sat_with_fallback(const std::vector<z3::expr>& fp,const std::vector<z3::expr>& exact) const
        {
            if(exact.empty()) return true;
            const bool full_abstract_cover=!fp.empty()&&fp.size()==exact.size();
            if(full_abstract_cover&&is_sat(fp)) return true;
            return is_sat(exact);
        }
private: 
    EntailmentPipeline exact_;std::unordered_map<std::string,z3::expr> vars_;
    static bool is_abstractable(const z3::expr& expr)
        {
            if(expr.is_true()||expr.is_false()||expr.is_numeral()) return true;
            if(expr.is_const()) return expr.is_bool()||expr.is_real()||expr.is_int();
            for(unsigned i=0;i<expr.num_args();++i)
                if(!is_abstractable(expr.arg(i))) return false;
            switch(expr.decl().decl_kind()){
            case Z3_OP_NOT:
            case Z3_OP_AND:
            case Z3_OP_OR:
            case Z3_OP_IMPLIES:
            case Z3_OP_ITE:
            case Z3_OP_EQ:
            case Z3_OP_DISTINCT:
            case Z3_OP_LE:
            case Z3_OP_LT:
            case Z3_OP_GE:
            case Z3_OP_GT:
            case Z3_OP_UMINUS:
            case Z3_OP_TO_REAL:
            case Z3_OP_ADD:
            case Z3_OP_SUB:
            case Z3_OP_MUL:
            case Z3_OP_DIV:
                return true;
            default:
                return false;
            }
        }
    static bool is_sat(const std::vector<z3::expr>& a)
        {
            if(a.empty()) return true;
            z3::solver s(a.front().ctx());
            for(const auto& e:a) s.add(e);
            return s.check()==z3::sat;
        }
    static bool is_sat_with_extra(const std::vector<z3::expr>& a,const z3::expr& x)
        {
            z3::solver s(x.ctx());
            for(const auto& e:a) s.add(e);
            s.add(x);
            return s.check()==z3::sat;
        }
};
} // namespace SMT::Real
