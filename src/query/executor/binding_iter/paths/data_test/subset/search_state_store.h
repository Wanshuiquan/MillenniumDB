#pragma once

#include <cstddef>
#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <type_traits>
#include <unordered_set>
#include <utility>

#include "graph_models/object_id.h"
#include "z3++.h"

namespace Paths::DataTest {

// Owns exactly one PathState for every state retained in the subset visited
// set. A duplicate candidate's temporary path is destroyed immediately.
template<typename State>
class SubsetSearchStateStore {
public:
    using PathState = std::remove_const_t<std::remove_pointer_t<
            decltype(std::declval<State>().path_state)>>;

    SubsetSearchStateStore() = default;
    SubsetSearchStateStore(const SubsetSearchStateStore&) = delete;
    SubsetSearchStateStore& operator=(const SubsetSearchStateStore&) = delete;

    ~SubsetSearchStateStore() { clear(); }

    std::pair<State*, bool> emplace(
            ObjectId node_id,
            ObjectId type_id,
            ObjectId edge_id,
            bool inverse_dir,
            const PathState* prev_state,
            uint32_t automaton_state,
            const z3::ast_vector_tpl<z3::expr>& formulas,
            const std::map<std::string, int64_t>& reg_vals)
    {
        auto path_state = std::make_unique<PathState>(
                node_id, type_id, edge_id, inverse_dir, prev_state);
        State state(path_state.get(), automaton_state);
        for (const auto& formula : formulas) state.formulas.push_back(formula);
        state.reg_vals = reg_vals;

        auto [it, inserted] = states_.emplace(state);
        if (inserted) path_state.release();
        return {const_cast<State*>(&*it), inserted};
    }

    void clear() {
        for (const auto& state : states_) delete state.path_state;
        states_.clear();
    }

    std::size_t size() const { return states_.size(); }
    std::size_t owned_path_count() const { return states_.size(); }

private:
    std::unordered_set<State> states_;
};

} // namespace Paths::DataTest
