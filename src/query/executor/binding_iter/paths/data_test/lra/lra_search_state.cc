//
// Created by heyang-li on 4/24/26.
//

#include "lra_search_state.h"

using namespace Paths::DataTest;





int MacroState::update_bound(std::tuple<Bound, int64_t, z3::expr> bound) {
    auto type = std::get<0>(bound);
    auto key = std::get<1>(bound);
    auto value = std::get<2>(bound);
    collected_expr.push_back(key);

    switch (type) {
        case Le: {
            if (upper_bounds.find(key) == upper_bounds.end()) {
                upper_bounds[key] = value.as_double();
            }
            else {
                double old_bound = upper_bounds[key];
                double new_bound = value.as_double();
                if (new_bound < old_bound) upper_bounds[key] = new_bound;
            }
            return 1;
        }
        case Ge: {
            if (lower_bounds.find(key) == lower_bounds.end()) {
                lower_bounds[key] = value.as_double();
            }
            else {
                double old_bound = lower_bounds[key];
                double new_bound = value.as_double();
                if (new_bound > old_bound) lower_bounds[key] = new_bound;
            }
            return 1;
        }
        case EQ: {
            if (eq_vals.find(key) == eq_vals.end()) {
                eq_vals[key] = value.as_double();
                return 1;
            }
            else {
                double old_bound = eq_vals[key];
                double new_bound = value.as_double();
                return int(new_bound == old_bound);
            }
        }
        default: return 0;
    }
}

void MacroState::initialize_from(const Paths::DataTest::MacroState &other) {
    path_state = other.path_state;
    automaton_state = other.automaton_state;
    upper_bounds = other.upper_bounds;
    lower_bounds = other.lower_bounds;
    eq_vals = other.eq_vals;
    collected_expr = other.collected_expr;
}

void MacroState::initialize(const Paths::DataTest::PathState *path, uint32_t state) {
    path_state = path;
    automaton_state = state;
    upper_bounds.clear();
    lower_bounds.clear();
    eq_vals.clear();
    collected_expr.clear();
}

