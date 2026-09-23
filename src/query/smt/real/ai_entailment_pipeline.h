#pragma once
#include <unordered_map>
#include <vector>
#include "query/smt/smt_ctx.h"
#include "query/smt/real/entailment_pipeline.h"
#include "query/smt/real/floating_point_rewriter.h"
#include "query/smt/real/nra_abstract_domain.h"
namespace SMT::Real {
class AIEntailmentPipeline {
public: 
explicit AIEntailmentPipeline(SMT::SolverCheck checker = {}) : exact_(std::move(checker)) { }

AtomDecision evaluate_and_update(std::vector<z3::expr>& fp,std::vector<z3::expr>& exact,const z3::expr& atom)
        {
            return get_smt_ctx().time_real_ai_entailment([&]() {
                const auto previous_exact_size = exact.size();
                const bool atom_fits = is_abstractable(atom)
                                       && NRAAbstractDomain::fits_binary64(NRAAbstractDomain::infer(atom));
                const bool full_abstract_cover = atom_fits && fp.size() == previous_exact_size;

                // All semantic decisions, including UNKNOWN handling, are made
                // by the exact real-arithmetic pipeline.
                std::vector<z3::expr> unused_bounded;
                const auto decision = exact_.evaluate_and_update(unused_bounded, exact, atom);
                if (decision != AtomDecision::Keep) return decision;

                if (!bounded_disabled_ && full_abstract_cover) {
                    try {
                        auto bounded_atom = FloatingPointRewriter64::rewrite(atom, vars_);
                        (void)is_sat_with_extra(fp, bounded_atom); // hint only
                        fp.push_back(bounded_atom);
                    } catch (...) {
                        bounded_disabled_ = true;
                        fp.clear();
                    }
                } else {
                    fp.clear();
                }
                return AtomDecision::Keep;
            });
        }

    SMT::CheckStatus check_sat_status(const std::vector<z3::expr>& fp,const std::vector<z3::expr>& exact) const
        {
            return get_smt_ctx().time_real_ai_entailment([&]() {
                (void)fp;
                return exact_.check_sat_status(exact);
            });
        }
private: 
    EntailmentPipeline exact_;std::unordered_map<std::string,z3::expr> vars_;
    bool bounded_disabled_ = false;
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
    static SMT::CheckStatus is_sat_with_extra(const std::vector<z3::expr>& a,const z3::expr& x)
        {
            z3::solver s(x.ctx());
            for(const auto& e:a) s.add(e);
            s.add(x);
            return SMT::SolverCheck {}(s);
        }
};
} // namespace SMT::Real
