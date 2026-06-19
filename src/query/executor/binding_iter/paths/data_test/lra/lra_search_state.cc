//
// Created by heyang-li on 4/24/26.
//

#include "lra_search_state.h"

#include <algorithm>

using namespace Paths::DataTest::LRA;





int MacroState::update_bound(std::tuple<Bound, int64_t, z3::expr> bound) {
    auto type = std::get<0>(bound);
    auto key = std::get<1>(bound);
    auto value = std::get<2>(bound);
    collected_expr.push_back(key);

    switch (type) {
        case Gt: {
            double new_bound = value.as_double();
            auto upper_it = upper_bounds.find(key);
            if (upper_it != upper_bounds.end() && new_bound >= upper_it->second) {
                return 0;
            }
            auto eq_it = eq_vals.find(key);
            if (eq_it != eq_vals.end() && eq_it->second <= new_bound) {
                return 0;
            }
            // Always update lower_bounds to the best (max) bound
            if (lower_bounds.find(key) == lower_bounds.end()) {
                lower_bounds[key] = new_bound;
            } else if (new_bound > lower_bounds[key]) {
                lower_bounds[key] = new_bound;
            }
            // Always record the strict inequality bound
            auto gt_it = gt_vals.find(key);
            if (gt_it == gt_vals.end() || new_bound > gt_it->second) {
                gt_vals[key] = new_bound;
            }

            auto final_lower = lower_bounds[key];
            if (eq_it != eq_vals.end() && eq_it->second <= final_lower) {
                return 0;
            }
            if (upper_it != upper_bounds.end() && upper_it->second <= final_lower) {
                return 0;
            }
            if (eq_it != eq_vals.end()) {
                auto neq_it = neq_vals.find(key);
                if (neq_it != neq_vals.end()) {
                    auto it = std::find(neq_it->second.begin(), neq_it->second.end(), eq_it->second);
                    if (it != neq_it->second.end()) {
                        return 0;
                    }
                }
            }
            return 1;
        }

        case Lt: {
            double new_bound = value.as_double();
            auto lower_it = lower_bounds.find(key);
            if (lower_it != lower_bounds.end() && new_bound <= lower_it->second) {
                return 0;
            }
            auto eq_it = eq_vals.find(key);
            if (eq_it != eq_vals.end() && eq_it->second >= new_bound) {
                return 0;
            }
            // Always update upper_bounds to the best (min) bound
            if (upper_bounds.find(key) == upper_bounds.end()) {
                upper_bounds[key] = new_bound;
            } else if (new_bound < upper_bounds[key]) {
                upper_bounds[key] = new_bound;
            }
            // Always record the strict inequality bound
            auto lt_it = lt_vals.find(key);
            if (lt_it == lt_vals.end() || new_bound < lt_it->second) {
                lt_vals[key] = new_bound;
            }
   
            auto final_upper = upper_bounds[key];
            if (eq_it != eq_vals.end() && eq_it->second >= final_upper) {
                return 0;
            }
            if (lower_it != lower_bounds.end() && lower_it->second >= final_upper) {
                return 0;
            }
            if (eq_it != eq_vals.end()) {
                auto neq_it = neq_vals.find(key);
                if (neq_it != neq_vals.end()) {
                    auto it = std::find(neq_it->second.begin(), neq_it->second.end(), eq_it->second);
                    if (it != neq_it->second.end()) {
                        return 0;
                    }
                }
            }
            return 1;
        }
        case Le: {
            double new_bound = value.as_double();
            auto lower_it = lower_bounds.find(key);
            if (lower_it != lower_bounds.end() && new_bound < lower_it->second) {
                return 0;
            }
            auto eq_it = eq_vals.find(key);
            if (eq_it != eq_vals.end() && eq_it->second > new_bound) {
                return 0;
            }
            if (upper_bounds.find(key) == upper_bounds.end()) {
                upper_bounds[key] = new_bound;
            }
            else {
                double old_bound = upper_bounds[key];
                if (new_bound < old_bound) upper_bounds[key] = new_bound;
            }

            auto final_upper = upper_bounds[key];
            if (eq_it != eq_vals.end() && eq_it->second > final_upper) {
                return 0;
            }
            if (lower_it != lower_bounds.end() && lower_it->second > final_upper) {
                return 0;
            }
            if (eq_it != eq_vals.end()) {
                auto neq_it = neq_vals.find(key);
                if (neq_it != neq_vals.end()) {
                    auto it = std::find(neq_it->second.begin(), neq_it->second.end(), eq_it->second);
                    if (it != neq_it->second.end()) {
                        return 0;
                    }
                }
            }
            return 1;
        }
        case Ge: {
            double new_bound = value.as_double();
            auto upper_it = upper_bounds.find(key);
            if (upper_it != upper_bounds.end() && new_bound > upper_it->second) {
                return 0;
            }
            auto eq_it = eq_vals.find(key);
            if (eq_it != eq_vals.end() && eq_it->second < new_bound) {
                return 0;
            }
            if (lower_bounds.find(key) == lower_bounds.end()) {
                lower_bounds[key] = new_bound;
            }
            else {
                double old_bound = lower_bounds[key];
                if (new_bound > old_bound) lower_bounds[key] = new_bound;
            }

            auto final_lower = lower_bounds[key];
            if (eq_it != eq_vals.end() && eq_it->second < final_lower) {
                return 0;
            }
            if (upper_it != upper_bounds.end() && upper_it->second < final_lower) {
                return 0;
            }
            if (eq_it != eq_vals.end()) {
                auto neq_it = neq_vals.find(key);
                if (neq_it != neq_vals.end()) {
                    auto it = std::find(neq_it->second.begin(), neq_it->second.end(), eq_it->second);
                    if (it != neq_it->second.end()) {
                        return 0;
                    }
                }
            }
            return 1;
        }
        case EQ: {
            double new_bound = value.as_double();
            auto upper_it = upper_bounds.find(key);
            if (upper_it != upper_bounds.end() && new_bound > upper_it->second) {
                return 0;
            }
            auto lower_it = lower_bounds.find(key);
            if (lower_it != lower_bounds.end() && new_bound < lower_it->second) {
                return 0;
            }
            auto neq_it = neq_vals.find(key);
            if (neq_it != neq_vals.end()) {
                auto it = std::find(neq_it->second.begin(), neq_it->second.end(), new_bound);
                if (it != neq_it->second.end()) {
                    return 0;
                }
            }
            if (eq_vals.find(key) == eq_vals.end()) {
                eq_vals[key] = new_bound;
                return 1;
            }
            else {
                double old_bound = eq_vals[key];
                return int(new_bound == old_bound);
            }
        }
        case Ne: {
            double new_bound = value.as_double();
            auto eq_it = eq_vals.find(key);
            if (eq_it != eq_vals.end() && eq_it->second == new_bound) {
                return 0;
            }

            auto& forbidden_values = neq_vals[key];
            auto it = std::find(forbidden_values.begin(), forbidden_values.end(), new_bound);
            if (it == forbidden_values.end()) {
                forbidden_values.push_back(new_bound);
            }

            auto upper_it = upper_bounds.find(key);
            auto lower_it = lower_bounds.find(key);
            if (upper_it != upper_bounds.end() && lower_it != lower_bounds.end()) {
                if (upper_it->second == lower_it->second && upper_it->second == new_bound) {
                    return 0;
                }
            }
            return 1;
        }
        default: return 0;
    }
}

void MacroState::initialize_from(const MacroState &other) {
    path_state = other.path_state;
    automaton_state = other.automaton_state;
    upper_bounds = other.upper_bounds;
    lower_bounds = other.lower_bounds;
    eq_vals = other.eq_vals;
    neq_vals = other.neq_vals;
    collected_expr = other.collected_expr;
}

void MacroState::initialize(const Paths::DataTest::PathState *path, uint32_t state) {
    path_state = path;
    automaton_state = state;
    upper_bounds.clear();
    lower_bounds.clear();
    eq_vals.clear();
    neq_vals.clear();
    collected_expr.clear();
}

