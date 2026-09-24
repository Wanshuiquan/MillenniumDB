#pragma once

#include <optional>
#include <stdexcept>
#include <unordered_map>
#include <vector>

#include "query/smt/real/entailment_pipeline.h"
#include "query/smt/real/floating_point_rewriter.h"
#include "query/smt/smt_ctx.h"

namespace SMT::Real {

class AIEntailmentPipeline {
public:
    explicit AIEntailmentPipeline(
            SMT::SolverCheck exact_check = {},
            SMT::SolverCheck bounded_check = {})
        : exact_check_(std::move(exact_check)),
          bounded_check_(std::move(bounded_check)) { }

    AtomDecision evaluate_and_update(
            std::vector<z3::expr>& bounded,
            std::vector<z3::expr>& exact,
            const z3::expr& atom)
    {
        return get_smt_ctx().time_real_ai_entailment([&]() {
            if (atom.is_true()) return AtomDecision::Redundant;
            if (atom.is_false()) return AtomDecision::Inconsistent;

            const bool full_bounded_cover = !bounded_disabled_
                                         && bounded.size() == exact.size();
            const auto counterexample = relation_status(
                    bounded, exact, !atom, full_bounded_cover);
            if (counterexample == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (counterexample == SMT::CheckStatus::Unsat) {
                return AtomDecision::Redundant;
            }

            const auto consistent = relation_status(
                    bounded, exact, atom, full_bounded_cover && !bounded_disabled_);
            if (consistent == SMT::CheckStatus::Unknown) {
                throw SMT::SolverUnknown {};
            }
            if (consistent == SMT::CheckStatus::Unsat) {
                return AtomDecision::Inconsistent;
            }

            if (full_bounded_cover && !bounded_disabled_) {
                try {
                    bounded.push_back(FloatingPointRewriter64::rewrite(
                            atom, bounded_vars_, source_vars_));
                } catch (...) {
                    disable_bounded(bounded);
                }
            } else {
                bounded.clear();
            }
            exact.push_back(atom);
            return AtomDecision::Keep;
        });
    }

    SMT::CheckStatus check_sat_status(
            const std::vector<z3::expr>& bounded,
            const std::vector<z3::expr>& exact) const
    {
        return get_smt_ctx().time_real_ai_entailment([&]() {
            if (!bounded_disabled_ && bounded.size() == exact.size()) {
                try {
                    const auto candidate = validated_bounded_status(
                            bounded, std::nullopt, exact, std::nullopt);
                    if (candidate == SMT::CheckStatus::Sat) {
                        return SMT::CheckStatus::Sat;
                    }
                } catch (...) {
                    // A final bounded check is still only a hint. Any model,
                    // decoding or solver failure falls back to exact Real.
                }
            }
            return exact_status(exact, std::nullopt);
        });
    }

private:
    SMT::SolverCheck exact_check_;
    SMT::SolverCheck bounded_check_;
    std::unordered_map<std::string, z3::expr> bounded_vars_;
    std::unordered_map<std::string, z3::expr> source_vars_;
    bool bounded_disabled_ = false;

    void disable_bounded(std::vector<z3::expr>& bounded) {
        bounded_disabled_ = true;
        bounded.clear();
        bounded_vars_.clear();
        source_vars_.clear();
    }

    SMT::CheckStatus relation_status(
            std::vector<z3::expr>& bounded,
            const std::vector<z3::expr>& exact,
            const z3::expr& extra,
            bool try_bounded)
    {
        if (try_bounded) {
            try {
                const auto bounded_extra = FloatingPointRewriter64::rewrite(
                        extra, bounded_vars_, source_vars_);
                const auto candidate = validated_bounded_status(
                        bounded, bounded_extra, exact, extra);
                if (candidate == SMT::CheckStatus::Sat) {
                    return SMT::CheckStatus::Sat;
                }
                // Bounded UNSAT/UNKNOWN and candidate-validation failure are
                // deliberately inconclusive for the original Real theory.
            } catch (...) {
                disable_bounded(bounded);
            }
        }
        return exact_status(exact, extra);
    }

    SMT::CheckStatus validated_bounded_status(
            const std::vector<z3::expr>& bounded,
            const std::optional<z3::expr>& bounded_extra,
            const std::vector<z3::expr>& exact,
            const std::optional<z3::expr>& exact_extra) const
    {
        z3::context* context = nullptr;
        if (bounded_extra) {
            context = &bounded_extra->ctx();
        } else if (!bounded.empty()) {
            context = &bounded.front().ctx();
        } else {
            // The empty formula is exactly SAT; there is no candidate model to
            // decode and no reason to invoke a bounded solver.
            return exact.empty() ? SMT::CheckStatus::Sat : SMT::CheckStatus::Unknown;
        }

        z3::solver bounded_solver(*context);
        for (const auto& expression : bounded) bounded_solver.add(expression);
        if (bounded_extra) bounded_solver.add(*bounded_extra);
        for (const auto& [name, variable] : bounded_vars_) {
            (void)name;
            bounded_solver.add(!variable.mk_is_nan() && !variable.mk_is_inf());
        }
        if (bounded_check_(bounded_solver) != SMT::CheckStatus::Sat) {
            return SMT::CheckStatus::Unknown;
        }

        // A custom checker can report SAT without actually running the solver;
        // model() then throws and the caller performs an exact fallback.
        const auto model = bounded_solver.get_model();
        if (exact.empty() && !exact_extra) return SMT::CheckStatus::Sat;
        z3::solver validation(exact_extra ? exact_extra->ctx() : exact.front().ctx());
        for (const auto& expression : exact) validation.add(expression);
        if (exact_extra) validation.add(*exact_extra);
        for (const auto& [name, bounded_variable] : bounded_vars_) {
            const auto source = source_vars_.find(name);
            if (source == source_vars_.end()) {
                throw std::invalid_argument("missing source variable for binary64 candidate");
            }
            const auto value = model.eval(bounded_variable, true);
            if (Z3_fpa_is_numeral_nan(value.ctx(), value)
                    || Z3_fpa_is_numeral_inf(value.ctx(), value)) {
                return SMT::CheckStatus::Unknown;
            }
            const auto exact_value = z3::to_expr(
                    value.ctx(), Z3_mk_fpa_to_real(value.ctx(), value));
            const auto source_value = source->second.is_int()
                                    ? z3::to_real(source->second)
                                    : source->second;
            validation.add(source_value == exact_value);
        }
        return exact_check_(validation);
    }

    SMT::CheckStatus exact_status(
            const std::vector<z3::expr>& exact,
            const std::optional<z3::expr>& extra) const
    {
        if (exact.empty() && !extra) return SMT::CheckStatus::Sat;
        z3::solver solver(extra ? extra->ctx() : exact.front().ctx());
        for (const auto& expression : exact) solver.add(expression);
        if (extra) solver.add(*extra);
        return exact_check_(solver);
    }
};

} // namespace SMT::Real
