#pragma once

#include <memory>
#include <vector>

#include "graph_models/object_id.h"

namespace Paths { namespace AllShortest {

struct SearchState;
struct PathIter;

// Holds relevant information from previous transitions
struct IterTransition {
    const SearchState* const previous;
    bool inverse_direction;
    ObjectId type_id;
    std::unique_ptr<IterTransition> next;

    IterTransition(const SearchState* previous, bool inverse_direction, ObjectId type_id) :
        previous          (previous),
        inverse_direction (inverse_direction),
        type_id           (type_id),
        next              (nullptr) { }
};

// Iterates over all previous transitions of a state
struct PathIter {
    std::unique_ptr<IterTransition> begin;
    IterTransition* end;
    IterTransition* current;

    PathIter() :
        begin   (nullptr),
        end     (nullptr),
        current (nullptr) { }

    PathIter(const SearchState* previous, bool inverse_direction, ObjectId type_id) :
        begin   (std::make_unique<IterTransition>(previous, inverse_direction, type_id)),
        end     (begin.get()),
        current (nullptr) { }

    void add(const SearchState* previous, bool inverse_direction, ObjectId type_id);
    void start_enumeration();
    bool next();
};

struct SearchState {
    const ObjectId node_id;
    const uint32_t automaton_state;
    const uint32_t distance;
    mutable PathIter path_iter;

    SearchState(ObjectId node_id, uint32_t automaton_state, uint32_t distance) :
        node_id         (node_id),
        automaton_state (automaton_state),
        distance        (distance),
        path_iter       (PathIter()) { }

    SearchState(ObjectId           node_id,
                uint32_t           automaton_state,
                uint32_t           distance,
                const SearchState* previous,
                bool               inverse_direction,
                ObjectId           type_id) :
    node_id         (node_id),
    automaton_state (automaton_state),
    distance        (distance),
    path_iter       (PathIter(previous, inverse_direction, type_id)) { }

    bool operator==(const SearchState& other) const {
        return automaton_state == other.automaton_state && node_id == other.node_id;
    }

    void print(std::ostream& os,
               void (*print_node) (std::ostream&, ObjectId),
               void (*print_edge) (std::ostream&, ObjectId, bool inverse),
               bool begin_at_left) const;
};

}} // namespace Paths::AllShortest

// For unordered set
template<>
struct std::hash<Paths::AllShortest::SearchState> {
    std::size_t operator() (const Paths::AllShortest::SearchState& lhs) const {
        return lhs.automaton_state ^ lhs.node_id.id;
    }
};
