#include <iostream>
#include <set>
#include <unordered_map>
#include <vector>

#include "query/executor/binding_iter/paths/data_test/model/integer/integer_search_state.h"
#include "query/executor/binding_iter/paths/data_test/model/real/real_search_state.h"
#include "query/executor/binding_iter/paths/data_test/model/macro_state_antichain.h"
#include "query/executor/binding_iter/paths/data_test/model_with_ai/integer/integer_search_state.h"
#include "query/executor/binding_iter/paths/data_test/model_with_ai/real/real_search_state.h"
#include "query/executor/binding_iter/paths/data_test/qe/lia/lia_search_state.h"
#include "query/executor/binding_iter/paths/data_test/qe/lra/lra_search_state.h"
#include "query/executor/binding_iter/paths/data_test/subset/integer/search_state.h"
#include "query/executor/binding_iter/paths/data_test/subset/search_state_store.h"
#include "query/smt/int/abstract_rewriter.h"
#include "query/smt/fixed_numeric_policy.h"
#include "query/smt/real/ai_entailment_pipeline.h"
#include "query/smt/real/floating_point_rewriter.h"
#include "query/smt/real/nra_abstract_domain.h"
#include "query/parser/paths/regular_path_expr.h"

namespace {

bool check(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAILED: " << message << '\n';
        return false;
    }
    return true;
}

enum class ConstraintRelation { Equivalent, LeftImpliesRight, Incomparable };

ConstraintRelation relation(z3::context& ctx, const z3::expr& left, const z3::expr& right) {
    z3::solver left_implies_right(ctx);
    left_implies_right.add(left && !right);
    z3::solver right_implies_left(ctx);
    right_implies_left.add(right && !left);
    const bool left_implies = left_implies_right.check() == z3::unsat;
    const bool right_implies = right_implies_left.check() == z3::unsat;
    if (left_implies && right_implies) return ConstraintRelation::Equivalent;
    if (left_implies) return ConstraintRelation::LeftImpliesRight;
    return ConstraintRelation::Incomparable;
}

bool constraint_relation_cases_are_distinguished() {
    z3::context ctx;
    const auto x = ctx.int_const("x");
    return check(relation(ctx, x >= 0, x > -1) == ConstraintRelation::Equivalent,
                 "equivalent integer constraints must be identified")
        && check(relation(ctx, x == 0, x >= 0) == ConstraintRelation::LeftImpliesRight,
                 "the stricter constraint must imply the weaker constraint")
        && check(relation(ctx, x < 0, x > 0) == ConstraintRelation::Incomparable,
                 "incomparable constraints must be recognized");
}

bool macro_states_keep_incomparable_constraints() {
    z3::context ctx;
    const auto x = ctx.int_const("x");
    Paths::DataTest::PathState path1(ObjectId(1), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState path2(ObjectId(1), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::IntegerModel::MacroStateInt left {};
    Paths::DataTest::IntegerModel::MacroStateInt right {};
    left.path_state = &path1;
    right.path_state = &path2;
    left.automaton_state = right.automaton_state = 7;
    left.collected_expr_int.push_back(x == 0);
    right.collected_expr_int.push_back(x == 1);

    Paths::DataTest::MacroStateAntichain<Paths::DataTest::IntegerModel::MacroStateInt> visited;
    visited.emplace(left);
    const auto inserted = visited.emplace(right);
    return check(inserted.second && visited.size() == 2,
                 "incomparable constraints at the same product location must both be retained");
}

bool real_macro_states_use_the_same_semantic_antichain_contract() {
    z3::context ctx;
    const auto x = ctx.real_const("real_x");
    Paths::DataTest::PathState path1(ObjectId(2), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState path2(ObjectId(2), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::RealModel::MacroStateReal left {};
    Paths::DataTest::RealModel::MacroStateReal right {};
    left.path_state = &path1;
    right.path_state = &path2;
    left.automaton_state = right.automaton_state = 8;
    left.collected_expr_int.push_back(x < 0);
    right.collected_expr_int.push_back(x > 0);
    Paths::DataTest::MacroStateAntichain<Paths::DataTest::RealModel::MacroStateReal> visited;
    visited.emplace(left);
    visited.emplace(right);
    return check(visited.size() == 2, "real incomparable constraints must both be retained");
}

bool macro_state_antichain_handles_equivalence_and_one_way_entailment() {
    z3::context ctx;
    const auto x = ctx.int_const("antichain_x");
    Paths::DataTest::PathState weak_path(ObjectId(3), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState strong_path(ObjectId(3), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::IntegerModel::MacroStateInt weak {};
    Paths::DataTest::IntegerModel::MacroStateInt strong {};
    weak.path_state = &weak_path;
    strong.path_state = &strong_path;
    weak.automaton_state = strong.automaton_state = 9;
    weak.collected_expr_int.push_back(x >= 0);
    strong.collected_expr_int.push_back(x > 0);

    Paths::DataTest::MacroStateAntichain<Paths::DataTest::IntegerModel::MacroStateInt> visited;
    visited.emplace(weak);
    const auto subsumed = visited.emplace(strong);
    if (!check(!subsumed.second && visited.size() == 1,
               "a weaker state must subsume a stronger state")) return false;
    if (!check(Paths::DataTest::surviving_path(subsumed) == &weak_path,
               "a rejected candidate must return the surviving state's witness")) return false;

    Paths::DataTest::IntegerModel::MacroStateInt equivalent = weak;
    equivalent.path_state = &strong_path;
    equivalent.collected_expr_int.clear();
    equivalent.collected_expr_int.push_back(!(x < 0));
    const auto duplicate = visited.emplace(equivalent);
    return check(!duplicate.second && visited.size() == 1,
                 "equivalent states must share one antichain representative");
}

bool integer_division_rewrite_preserves_negative_semantics() {
    z3::context ctx;
    const auto x = ctx.int_const("x");
    const auto quotient = ctx.int_val(-5) / 2;
    const auto formula = (x == -5) && (x / 2 == quotient);
    z3::solver exact(ctx);
    exact.add(formula);

    z3::context bv_ctx;
    std::unordered_map<std::string, z3::expr> vars;
    const auto rewritten = SMT::Int::AbstractRewriter64::rewrite_int_atom_to_bv(formula, bv_ctx, vars);
    z3::solver bounded(bv_ctx);
    bounded.add(rewritten);

    return check(quotient.simplify() == ctx.int_val(-3), "integer division of -5 by 2 must be -3")
        && check(exact.check() == z3::sat, "source integer formula must have its exact quotient witness")
        && check(bounded.check() == z3::sat, "bounded rewrite must preserve the exact quotient witness");
}

bool integer_modulo_rewrite_preserves_negative_semantics() {
    z3::context ctx;
    const auto x = ctx.int_const("x");
    const auto remainder = z3::mod(ctx.int_val(-5), ctx.int_val(2));
    const auto formula = (x == -5) && (z3::mod(x, 2) == remainder);
    z3::solver exact(ctx);
    exact.add(formula);

    z3::context bv_ctx;
    std::unordered_map<std::string, z3::expr> vars;
    const auto rewritten = SMT::Int::AbstractRewriter64::rewrite_int_atom_to_bv(formula, bv_ctx, vars);
    z3::solver bounded(bv_ctx);
    bounded.add(rewritten);

    return check(remainder.simplify() == ctx.int_val(1), "integer modulo of -5 by 2 must be 1")
        && check(exact.check() == z3::sat, "source integer formula must have its exact remainder witness")
        && check(bounded.check() == z3::sat, "bounded rewrite must preserve the exact remainder witness");
}

bool integer_overflow_does_not_create_a_bounded_witness() {
    z3::context ctx;
    const auto x = ctx.int_const("x");
    const auto max = ctx.int_val("9223372036854775807");
    const auto min = ctx.int_val("-9223372036854775808");
    const auto formula = (x == max) && (x + 1 == min);
    z3::solver exact_oracle(ctx);
    std::vector<z3::expr> bounded_assumptions;
    std::vector<z3::expr> exact_assumptions;
    SMT::Int::EntailmentPipeline64 pipeline;
    const auto decision = pipeline.evaluate_and_update(
            exact_oracle,
            bounded_assumptions,
            exact_assumptions,
            formula);
    const bool exact_is_unsat = [&]() {
        z3::solver solver(ctx);
        solver.add(formula);
        return solver.check() == z3::unsat;
    }();
    std::vector<z3::expr> source_formula {formula};
    return check(exact_is_unsat, "unbounded integers must reject a signed-64-bit overflow witness")
        && check(decision == SMT::Int::AtomDecision::Inconsistent,
                 "the exact solver must reject a wrapping bounded witness immediately")
        && check(pipeline.check_sat_status(exact_oracle, bounded_assumptions, source_formula)
                         == SMT::CheckStatus::Unsat,
                 "a bounded SAT candidate must not override an UNSAT exact oracle");
}

bool bounded_unsat_falls_back_to_exact_integer_arithmetic() {
    z3::context ctx;
    z3::solver exact_solver(ctx);
    const auto x = ctx.int_const("fallback_x");
    const auto y = ctx.int_const("fallback_y");
    const auto max = ctx.int_val("9223372036854775807");
    SMT::Int::EntailmentPipeline64 pipeline;
    std::vector<z3::expr> bounded;
    std::vector<z3::expr> exact;
    const std::vector<z3::expr> assumptions {x == max, y == 1};
    for (const auto& atom : assumptions) {
        if (!check(pipeline.evaluate_and_update(exact_solver, bounded, exact, atom)
                           == SMT::Int::AtomDecision::Keep,
                   "bounded UNSAT must not reject an exact-SAT integer atom")) return false;
    }
    const auto overflow_sensitive = pipeline.evaluate_and_update(
            exact_solver, bounded, exact, x + y > max);
    if (!check(overflow_sensitive == SMT::Int::AtomDecision::Redundant,
               "exact arithmetic must prove an overflow-sensitive consequence")) return false;
    return check(pipeline.check_sat_status(exact_solver, bounded, exact) == SMT::CheckStatus::Sat,
                 "the original integer theory must decide the overflow-sensitive formula");
}

bool real_ai_gate_falls_back_to_exact_arithmetic() {
    z3::context ctx;
    const auto x = ctx.real_const("x");
    std::vector<z3::expr> bounded;
    std::vector<z3::expr> exact;
    SMT::Real::AIEntailmentPipeline pipeline;
    const auto decision = pipeline.evaluate_and_update(bounded, exact, x + 1 == 3);
    z3::solver oracle(ctx);
    oracle.add(x + 1 == 3);
    return check(decision == SMT::Real::AtomDecision::Keep, "exact fallback should preserve a satisfiable real constraint")
        && check(oracle.check() == z3::sat, "the exact real constraint is satisfiable")
        && check(exact.size() == 1, "the exact constraint must be retained")
        && check(pipeline.check_sat_status(bounded, exact) == SMT::CheckStatus::Sat,
                 "the real pipeline must confirm the exact fallback result");
}

bool nested_boolean_constants_are_safe_bounded_hints() {
    z3::context ctx;
    z3::solver exact_solver(ctx);
    const auto x = ctx.int_const("boolean_constant_x");
    const auto atom = ctx.bool_val(true) && (x == 1);
    std::vector<z3::expr> bounded;
    std::vector<z3::expr> exact;
    SMT::Int::EntailmentPipeline64 pipeline;
    const auto decision = pipeline.evaluate_and_update(exact_solver, bounded, exact, atom);
    return check(decision == SMT::Int::AtomDecision::Keep,
                 "a nested true literal must not change the exact integer decision")
        && check(exact.size() == 1,
                 "the source formula containing true must remain in the exact constraints")
        && check(pipeline.check_sat_status(exact_solver, bounded, exact) == SMT::CheckStatus::Sat,
                 "a nested true literal must remain satisfiable through the pipeline");
}

bool bounded_hint_failure_falls_back_to_exact_integer_reasoning() {
    z3::context ctx;
    z3::solver exact_solver(ctx);
    const auto x = ctx.int_const("throwing_hint_x");
    const SMT::SolverCheck throwing_bounded([](z3::solver&) -> SMT::CheckStatus {
        throw std::runtime_error("synthetic bounded-solver failure");
    });
    SMT::Int::EntailmentPipeline64 pipeline(SMT::SolverCheck {}, throwing_bounded);
    std::vector<z3::expr> bounded;
    std::vector<z3::expr> exact;
    const auto decision = pipeline.evaluate_and_update(
            exact_solver, bounded, exact, ctx.bool_val(true) && (x == 7));
    return check(decision == SMT::Int::AtomDecision::Keep,
                 "a bounded hint exception must not alter the exact decision")
        && check(bounded.empty(), "a failing bounded hint must be disabled and discarded")
        && check(exact.size() == 1,
                 "the exact source formula must survive a bounded hint exception")
        && check(pipeline.check_sat_status(exact_solver, bounded, exact) == SMT::CheckStatus::Sat,
                 "exact satisfiability must remain available after disabling the hint");
}

struct NonBinary64TestPolicy {
    static constexpr unsigned integer_bit_width = 17;
    static constexpr unsigned floating_point_exponent_bits = 5;
    static constexpr unsigned floating_point_significand_bits = 11;
};

bool floating_point_numerals_use_the_configured_fp_sort() {
    z3::context ctx;
    std::unordered_map<std::string, z3::expr> variables;
    using TestRewriter = SMT::Real::FloatingPointRewriter<NonBinary64TestPolicy>;
    const auto variable = TestRewriter::rewrite(ctx.real_const("policy_real_x"), variables);
    const auto numeral = TestRewriter::rewrite(ctx.real_val("1.25"), variables);
    const auto variable_sort = variable.get_sort();
    const auto numeral_sort = numeral.get_sort();
    return check(Z3_is_eq_sort(ctx, variable_sort, numeral_sort),
                 "floating-point variables and numerals must use the same configured sort")
        && check(variable_sort.fpa_ebits() == NonBinary64TestPolicy::floating_point_exponent_bits,
                 "the configured floating-point exponent width must reach variables and numerals")
        && check(variable_sort.fpa_sbits() == NonBinary64TestPolicy::floating_point_significand_bits,
                 "the configured floating-point significand width must reach variables and numerals");
}

bool semantic_wiring_distinguishes_exact_and_bounded_hint_variants() {
    using Paths::SMTEntailmentPolicy;
    return check(Paths::get_smt_entailment_policy(PathSemantic::NIA_MODEL)
                         == SMTEntailmentPolicy::ExactInteger,
                 "NIA_MODEL must use the exact integer pipeline")
        && check(Paths::get_smt_entailment_policy(PathSemantic::NIA_MODEL_WITH_AI)
                         == SMTEntailmentPolicy::FixedInt64Hint,
                 "NIA_MODEL_WITH_AI must use the fixed-int64 hint pipeline")
        && check(Paths::get_smt_entailment_policy(PathSemantic::NRA_MODEL)
                         == SMTEntailmentPolicy::ExactReal,
                 "NRA_MODEL must use the exact real pipeline")
        && check(Paths::get_smt_entailment_policy(PathSemantic::NRA_MODEL_WITH_AI)
                         == SMTEntailmentPolicy::Binary64Hint,
                 "NRA_MODEL_WITH_AI must use the binary64 hint pipeline");
}

bool fixed_numeric_policy_is_explicit() {
    return check(SMT::FixedInt64Binary64Policy::integer_bit_width == 64,
                 "fixed integer policy must expose its width")
        && check(SMT::FixedInt64Binary64Policy::floating_point_exponent_bits == 11,
                 "binary64 exponent width must be explicit")
        && check(SMT::FixedInt64Binary64Policy::floating_point_significand_bits == 53,
                 "binary64 significand width must be explicit");
}

bool unknown_fails_integer_entailment_evaluation() {
    z3::context ctx;
    z3::solver solver(ctx);
    const auto x = ctx.int_const("unknown_x");
    const SMT::SolverCheck always_unknown([](z3::solver&) {
        return SMT::CheckStatus::Unknown;
    });
    SMT::Int::EntailmentPipeline64 pipeline(always_unknown);
    std::vector<z3::expr> bounded;
    std::vector<z3::expr> exact;
    bool failed = false;
    try {
        (void)pipeline.evaluate_and_update(solver, bounded, exact, x == 1);
    } catch (const SMT::SolverUnknown&) {
        failed = true;
    }
    const std::vector<z3::expr> source_formula {x == 1};
    return check(failed, "UNKNOWN during entailment must fail the current exploration")
        && check(exact.empty(), "an UNKNOWN entailment query must not mutate the exact state")
        && check(pipeline.check_sat_status(solver, bounded, source_formula) == SMT::CheckStatus::Unknown,
                 "UNKNOWN must be propagated by the satisfiability API");
}

bool unknown_terminates_the_integer_macro_state_call_chain() {
    z3::context ctx;
    z3::solver solver(ctx);
    const auto x = ctx.int_const("macro_unknown_x");
    Paths::DataTest::PathState path(ObjectId(5), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::Integer::MacroStateInt state {};
    state.path_state = &path;
    state.automaton_state = 11;
    state.collected_expr_int.push_back(x == 1);

    SMT::Int::EntailmentPipeline64 unknown_pipeline(SMT::SolverCheck(
            [](z3::solver&) { return SMT::CheckStatus::Unknown; }));
    const auto unknown_status = state.check_constraints(solver, unknown_pipeline);
    bool unknown_threw = false;
    try {
        (void)SMT::is_satisfiable_or_throw(unknown_status);
    } catch (const SMT::SolverUnknown&) {
        unknown_threw = true;
    }

    SMT::Int::EntailmentPipeline64 unsat_pipeline(SMT::SolverCheck(
            [](z3::solver&) { return SMT::CheckStatus::Unsat; }));
    const auto unsat_status = state.check_constraints(solver, unsat_pipeline);
    bool unsat_pruned = false;
    try {
        unsat_pruned = !SMT::is_satisfiable_or_throw(unsat_status);
    } catch (...) {
        return check(false, "UNSAT must prune rather than fail exploration");
    }
    Paths::DataTest::IntegerModel::MacroStateInt exact_state {};
    exact_state.path_state = &path;
    exact_state.automaton_state = 11;
    exact_state.collected_expr_int.push_back(x == 1);
    SMT::Int::ExactEntailmentPipeline exact_unknown_pipeline(SMT::SolverCheck(
            [](z3::solver&) { return SMT::CheckStatus::Unknown; }));
    const auto exact_unknown_status = exact_state.check_constraints(
            solver, exact_unknown_pipeline);

    return check(unknown_status == SMT::CheckStatus::Unknown,
                 "MacroState::check_constraints must propagate UNKNOWN")
        && check(unknown_threw, "the executor acceptance adapter must fail exploration on UNKNOWN")
        && check(unsat_status == SMT::CheckStatus::Unsat && unsat_pruned,
                 "UNSAT must remain an ordinary acceptance-pruning result")
        && check(exact_unknown_status == SMT::CheckStatus::Unknown,
                 "the exact integer MacroState call chain must also propagate UNKNOWN");
}

bool unknown_terminates_the_real_ai_macro_state_call_chain() {
    z3::context ctx;
    z3::solver solver(ctx);
    const auto x = ctx.real_const("real_macro_unknown_x");
    Paths::DataTest::PathState path(ObjectId(6), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::Real::MacroStateReal state {};
    state.path_state = &path;
    state.automaton_state = 12;
    state.collected_expr_int.push_back(x == 1);
    SMT::Real::AIEntailmentPipeline pipeline(SMT::SolverCheck(
            [](z3::solver&) { return SMT::CheckStatus::Unknown; }));
    std::vector<z3::expr> bounded;
    std::vector<z3::expr> exact;
    bool evaluation_failed = false;
    try {
        (void)pipeline.evaluate_and_update(bounded, exact, x == 1);
    } catch (const SMT::SolverUnknown&) {
        evaluation_failed = true;
    }
    const auto status = state.check_constraints(solver, pipeline);
    bool failed = false;
    try {
        (void)SMT::is_satisfiable_or_throw(status);
    } catch (const SMT::SolverUnknown&) {
        failed = true;
    }
    return check(status == SMT::CheckStatus::Unknown,
                 "real AI MacroState::check_constraints must propagate UNKNOWN")
        && check(evaluation_failed && exact.empty(),
                 "UNKNOWN during real AI entailment must fail without mutating exact state")
        && check(failed, "real AI executor acceptance must fail exploration on UNKNOWN");
}

bool unknown_fails_without_mutating_the_antichain() {
    z3::context ctx;
    const auto x = ctx.int_const("unknown_antichain_x");
    Paths::DataTest::PathState path1(ObjectId(4), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState path2(ObjectId(4), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::IntegerModel::MacroStateInt left {};
    Paths::DataTest::IntegerModel::MacroStateInt right {};
    left.path_state = &path1;
    right.path_state = &path2;
    left.automaton_state = right.automaton_state = 10;
    left.collected_expr_int.push_back(x == 1);
    right.collected_expr_int.push_back(x == 1);
    unsigned implication_checks = 0;
    Paths::DataTest::MacroStateAntichain<Paths::DataTest::IntegerModel::MacroStateInt> visited(
            SMT::SolverCheck([&](z3::solver& solver) {
                if (implication_checks++ == 0) return SMT::CheckStatus::Unknown;
                return SMT::to_check_status(solver.check());
            }));
    visited.emplace(left);
    bool failed = false;
    try {
        (void)visited.emplace(right);
    } catch (const SMT::SolverUnknown&) {
        failed = true;
    }
    if (!check(failed, "UNKNOWN implication must fail the current exploration")) return false;
    if (!check(visited.size() == 1,
               "a failed antichain insertion must leave the container size unchanged")) return false;

    const auto retry = visited.emplace(right);
    return check(!retry.second && Paths::DataTest::surviving_path(retry) == &path1,
                 "the original antichain representative must survive an UNKNOWN failure");
}

bool exact_real_unknown_failure_is_distinct_from_unsat_pruning() {
    z3::context ctx;
    z3::solver solver(ctx);
    const auto x = ctx.real_const("exact_real_unknown_x");
    Paths::DataTest::PathState path(ObjectId(7), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::RealModel::MacroStateReal state {};
    state.path_state = &path;
    state.automaton_state = 13;
    state.collected_expr_int.push_back(x == 1);

    const SMT::SolverCheck always_unknown(
            [](z3::solver&) { return SMT::CheckStatus::Unknown; });
    const auto unknown_status = state.check_constraints(
            solver, always_unknown, always_unknown);
    bool unknown_failed = false;
    try {
        (void)SMT::is_satisfiable_or_throw(unknown_status);
    } catch (const SMT::SolverUnknown&) {
        unknown_failed = true;
    }

    const SMT::SolverCheck always_unsat(
            [](z3::solver&) { return SMT::CheckStatus::Unsat; });
    const auto unsat_status = state.check_constraints(solver, always_unsat);
    bool unsat_pruned = false;
    try {
        unsat_pruned = !SMT::is_satisfiable_or_throw(unsat_status);
    } catch (...) {
        return check(false, "exact-real UNSAT must prune rather than fail exploration");
    }

    return check(unknown_status == SMT::CheckStatus::Unknown && unknown_failed,
                 "fallback UNKNOWN must propagate through the exact-real executor adapter")
        && check(unsat_status == SMT::CheckStatus::Unsat && unsat_pruned,
                 "exact-real UNSAT must remain ordinary acceptance pruning");
}

bool qe_lia_antichain_keeps_constraints_and_surviving_witness_aligned() {
    auto& smt = get_smt_ctx();
    smt.add_int_var("qe_lia_antichain_x");
    const auto x = smt.get_var("qe_lia_antichain_x");
    const auto x_id = smt.add_a_term(x);

    Paths::DataTest::PathState zero_path(
            ObjectId(20), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState one_path(
            ObjectId(20), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState duplicate_path(
            ObjectId(20), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::LIA::MacroState zero {};
    Paths::DataTest::LIA::MacroState one {};
    zero.path_state = &zero_path;
    one.path_state = &one_path;
    zero.automaton_state = one.automaton_state = 21;
    zero.eq_vals.emplace(x_id, 0);
    one.eq_vals.emplace(x_id, 1);
    zero.collected_expr.push_back(x_id);
    one.collected_expr.push_back(x_id);

    Paths::DataTest::MacroStateAntichain<Paths::DataTest::LIA::MacroState> visited;
    const auto first = visited.emplace(zero);
    const auto incomparable = visited.emplace(one);
    if (!check(first.second && incomparable.second && visited.size() == 2,
               "QE LIA states with one structural key and incompatible bounds must both survive")) {
        return false;
    }

    auto duplicate = zero;
    duplicate.path_state = &duplicate_path;
    const auto rejected = visited.emplace(duplicate);
    return check(!rejected.second && visited.size() == 2,
                 "an equivalent QE LIA state must reuse its semantic representative")
        && check(Paths::DataTest::surviving_path(rejected) == &zero_path,
                 "QE enum acceptance must use the stored representative's witness path");
}

bool qe_lra_antichain_keeps_incomparable_bounds() {
    auto& smt = get_smt_ctx();
    smt.add_real_var("qe_lra_antichain_x");
    const auto x = smt.get_var("qe_lra_antichain_x");
    const auto x_id = smt.add_a_term(x);

    Paths::DataTest::PathState negative_path(
            ObjectId(22), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::PathState positive_path(
            ObjectId(22), ObjectId(0), ObjectId(0), false, nullptr);
    Paths::DataTest::LRA::MacroState negative {};
    Paths::DataTest::LRA::MacroState positive {};
    negative.path_state = &negative_path;
    positive.path_state = &positive_path;
    negative.automaton_state = positive.automaton_state = 23;
    negative.lt_vals.emplace(x_id, 0.0);
    positive.gt_vals.emplace(x_id, 0.0);
    negative.collected_expr.push_back(x_id);
    positive.collected_expr.push_back(x_id);

    Paths::DataTest::MacroStateAntichain<Paths::DataTest::LRA::MacroState> visited;
    visited.emplace(negative);
    const auto inserted = visited.emplace(positive);
    return check(inserted.second && visited.size() == 2,
                 "QE LRA states with one structural key and incomparable bounds must both survive");
}

bool subset_store_isolates_siblings_and_owns_one_path_per_state() {
    using State = Paths::DataTest::NIA_SubsetOrder::SearchState;
    using Store = Paths::DataTest::SubsetSearchStateStore<State>;
    auto& smt = get_smt_ctx();
    smt.add_int_var("subset_store_x");
    const auto x = smt.get_var("subset_store_x");
    z3::ast_vector_tpl<z3::expr> formulas(*smt.get_context());
    formulas.push_back(x == 1);

    Store store;
    const std::map<std::string, int64_t> parent_registers {{"r", 1}};
    const auto first = store.emplace(
            ObjectId(30), ObjectId(0), ObjectId(0), false, nullptr,
            31, formulas, parent_registers);
    const auto duplicate = store.emplace(
            ObjectId(30), ObjectId(9), ObjectId(10), true, nullptr,
            31, formulas, parent_registers);
    if (!check(first.second && !duplicate.second && first.first == duplicate.first,
               "a duplicate subset state must return the retained container element")) {
        return false;
    }
    if (!check(store.size() == 1 && store.owned_path_count() == 1,
               "a rejected subset duplicate must not leak an extra PathState")) {
        return false;
    }

    State left(*first.first);
    State right(*first.first);
    left.reg_vals["r"] = 2;
    right.reg_vals["r"] = 3;
    if (!check(first.first->reg_vals.at("r") == 1
                       && left.reg_vals.at("r") == 2
                       && right.reg_vals.at("r") == 3,
               "each subset transition sibling must mutate an independent register copy")) {
        return false;
    }

    const auto left_inserted = store.emplace(
            ObjectId(32), ObjectId(0), ObjectId(11), false,
            first.first->path_state, 33, formulas, left.reg_vals);
    const auto right_inserted = store.emplace(
            ObjectId(32), ObjectId(0), ObjectId(12), false,
            first.first->path_state, 33, formulas, right.reg_vals);
    if (!check(left_inserted.second && right_inserted.second && store.size() == 3,
               "sibling subset states with distinct registers must remain distinct")) {
        return false;
    }

    store.clear();
    return check(store.size() == 0 && store.owned_path_count() == 0,
                 "clearing the subset store must release every retained PathState");
}

} // namespace

int main() {
    bool ok = true;
    ok = constraint_relation_cases_are_distinguished() && ok;
    ok = macro_states_keep_incomparable_constraints() && ok;
    ok = real_macro_states_use_the_same_semantic_antichain_contract() && ok;
    ok = macro_state_antichain_handles_equivalence_and_one_way_entailment() && ok;
    ok = integer_division_rewrite_preserves_negative_semantics() && ok;
    ok = integer_modulo_rewrite_preserves_negative_semantics() && ok;
    ok = integer_overflow_does_not_create_a_bounded_witness() && ok;
    ok = bounded_unsat_falls_back_to_exact_integer_arithmetic() && ok;
    ok = real_ai_gate_falls_back_to_exact_arithmetic() && ok;
    ok = nested_boolean_constants_are_safe_bounded_hints() && ok;
    ok = bounded_hint_failure_falls_back_to_exact_integer_reasoning() && ok;
    ok = floating_point_numerals_use_the_configured_fp_sort() && ok;
    ok = semantic_wiring_distinguishes_exact_and_bounded_hint_variants() && ok;
    ok = fixed_numeric_policy_is_explicit() && ok;
    ok = unknown_fails_integer_entailment_evaluation() && ok;
    ok = unknown_terminates_the_integer_macro_state_call_chain() && ok;
    ok = unknown_terminates_the_real_ai_macro_state_call_chain() && ok;
    ok = unknown_fails_without_mutating_the_antichain() && ok;
    ok = exact_real_unknown_failure_is_distinct_from_unsat_pruning() && ok;
    ok = qe_lia_antichain_keeps_constraints_and_surviving_witness_aligned() && ok;
    ok = qe_lra_antichain_keeps_incomparable_bounds() && ok;
    ok = subset_store_isolates_siblings_and_owns_one_path_per_state() && ok;
    return ok ? 0 : 1;
}
