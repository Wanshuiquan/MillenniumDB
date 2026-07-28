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
            if(!NRAAbstractDomain::fits_binary64(NRAAbstractDomain::infer(atom)))
            return exact_.evaluate_and_update(fp,exact,atom);
            auto f=FloatingPointRewriter64::rewrite(atom,vars_);
            if(entailed(fp,f)||entailed(exact,atom)) return AtomDecision::Redundant;
            if(inconsistent(fp,f)||inconsistent(exact,atom)) return AtomDecision::Inconsistent;
            fp.push_back(f);exact.push_back(atom);
            return AtomDecision::Keep;}
private: 
    EntailmentPipeline exact_;std::unordered_map<std::string,z3::expr> vars_;
    static bool entailed(const std::vector<z3::expr>& a,const z3::expr& x)
        {z3::solver s(x.ctx());
            for(const auto& e:a) s.add(e);
            s.add(!x);
            return s.check()==z3::unsat;
        }
    static bool inconsistent(const std::vector<z3::expr>& a,const z3::expr& x)
        {
            z3::solver s(x.ctx());
            for(const auto& e:a) s.add(e);
            s.add(x);
            return s.check()==z3::unsat;
        }
};
} // namespace SMT::Real
