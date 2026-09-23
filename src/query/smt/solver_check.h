#pragma once

#include <functional>
#include <stdexcept>
#include <utility>

#include "z3++.h"

namespace SMT {

enum class CheckStatus {
    Sat,
    Unsat,
    Unknown,
};

inline CheckStatus to_check_status(const z3::check_result& result) {
    if (result == z3::sat) return CheckStatus::Sat;
    if (result == z3::unsat) return CheckStatus::Unsat;
    return CheckStatus::Unknown;
}

class SolverUnknown final : public std::runtime_error {
public:
    SolverUnknown() : std::runtime_error("SMT solver returned unknown; exploration failed") { }
};

inline bool is_satisfiable_or_throw(CheckStatus status) {
    if (status == CheckStatus::Unknown) throw SolverUnknown {};
    return status == CheckStatus::Sat;
}

class SolverCheck {
public:
    using Function = std::function<CheckStatus(z3::solver&)>;

    SolverCheck() = default;
    explicit SolverCheck(Function function) : function_(std::move(function)) { }

    CheckStatus operator()(z3::solver& solver) const {
        if (function_) {
            return function_(solver);
        }
        return to_check_status(solver.check());
    }

private:
    Function function_;
};

} // namespace SMT
