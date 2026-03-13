//
// Created by lhy on 3/13/26.
//

#include "smt_unfixed_composite.h"
#include "graph_models/quad_model/quad_model.h"


using namespace  Paths;

bool SMTUnfixedComposite::set_next_starting_node() {
    while (true) {
        auto curr = iter.next();
        while (curr == nullptr) {
            current_start_transition++;
            if (current_start_transition < start_transitions.size()) {
                auto type_id = start_transitions[current_start_transition].type_id.id;
                std::array<uint64_t ,2> min_prop_ids{};
                std::array<uint64_t, 2> max_prop_ids{};
                max_prop_ids[0] = type_id;
                min_prop_ids[0] = type_id;
                max_prop_ids[1] = UINT64_MAX,
                        min_prop_ids[1] = 0;
                // only for quad model make sense
                iter = quad_model.label_node->get_range(
                        &get_query_ctx().thread_info.interruption_requested,
                        Record<2>(min_prop_ids),
                        Record<2>(max_prop_ids));
                idx_searches++;
            } else {
                return false;
            }
        }
        // we have a possible new start, check it has not visited before

        auto possible_start = (*curr)[1];

        if (last_start != possible_start && visited.find(possible_start) == visited.end()) {
            last_start = possible_start;
            visited.emplace(possible_start);
            return true;
        }
    }
}


void SMTUnfixedComposite::_begin(Binding& _parent_binding) {
    parent_binding = &_parent_binding;

    auto type_id = start_transitions[current_start_transition].type_id.id;
    std::array<uint64_t ,2> min_prop_ids{};
    std::array<uint64_t, 2> max_prop_ids{};
    max_prop_ids[0] = type_id;
    min_prop_ids[0] = type_id;
    max_prop_ids[1] = UINT64_MAX,
            min_prop_ids[1] = 0;
    // only for quad model make sense
    iter = quad_model.label_node->get_range(
            &get_query_ctx().thread_info.interruption_requested,
            Record<2>(min_prop_ids),
            Record<2>(max_prop_ids));
    idx_searches++;

    if (set_next_starting_node()) {
        parent_binding->add(start, ObjectId(last_start));
    } else {
        parent_binding->add(start, ObjectId::get_null());
    }
    child_iter->begin(_parent_binding);
}


bool SMTUnfixedComposite::_next() {
    while (current_start_transition < start_transitions.size()) {
        if (child_iter->next()) {
            return true;
        } else {
            if (set_next_starting_node()) {
                parent_binding->add(start, ObjectId(last_start));
                child_iter->reset();
            } else {
                return false;
            }
        }
    }
    return false;
}


void SMTUnfixedComposite::_reset() {
    visited.clear();

    current_start_transition = 0;
    last_start = ObjectId::get_null().id;

    auto type_id = start_transitions[current_start_transition].type_id.id;
    std::array<uint64_t ,2> min_prop_ids{};
    std::array<uint64_t, 2> max_prop_ids{};
    max_prop_ids[0] = type_id;
    min_prop_ids[0] = type_id;
    max_prop_ids[1] = UINT64_MAX,
            min_prop_ids[1] = 0;
    // only for quad model make sense
    iter = quad_model.label_node->get_range(
            &get_query_ctx().thread_info.interruption_requested,
            Record<2>(min_prop_ids),
            Record<2>(max_prop_ids));    idx_searches++;

    if (set_next_starting_node()) {
        parent_binding->add(start, ObjectId(last_start));
    } else {
        parent_binding->add(start, ObjectId::get_null());
    }
    child_iter->reset();
}


void SMTUnfixedComposite::print(std::ostream& os, int indent, bool stats) const {
    if (stats) {
        if (stats) {
            os << std::string(indent, ' ') << "[begin: " << stat_begin << " next: " << stat_next
               << " reset: " << stat_reset << " results: " << results << " idx_searches: " << idx_searches
               << "]\n";
        }
    }
    os << std::string(indent, ' ') << "Paths::UnfixedComposite(path_var: " << path_var
       << ", start: " << start << ", end: " << end << ")";

    child_iter->print(os, indent + 2, stats);
}