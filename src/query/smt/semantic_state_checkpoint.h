#pragma once

#include <utility>

namespace SMT {

// Transactional guard for path-search state. A successor may be copied while
// the guard is alive; the explored parent is restored before the next sibling.
template<typename State>
class SemanticStateCheckpoint {
public:
    explicit SemanticStateCheckpoint(State& state)
        : state_(state),
          exact_(state.collected_expr_int),
          bounded_(state.collected_expr_bv),
          registers_(state.reg_vals) { }

    SemanticStateCheckpoint(const SemanticStateCheckpoint&) = delete;
    SemanticStateCheckpoint& operator=(const SemanticStateCheckpoint&) = delete;

    ~SemanticStateCheckpoint() {
        state_.collected_expr_int = std::move(exact_);
        state_.collected_expr_bv = std::move(bounded_);
        state_.reg_vals = std::move(registers_);
    }

private:
    State& state_;
    decltype(std::declval<State>().collected_expr_int) exact_;
    decltype(std::declval<State>().collected_expr_bv) bounded_;
    decltype(std::declval<State>().reg_vals) registers_;
};

} // namespace SMT
