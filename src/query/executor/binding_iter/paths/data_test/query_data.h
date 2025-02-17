//
// Created by lhy on 9/19/24.
//

#ifndef MILLENNIUMDB_QUERY_DATA_H
#define MILLENNIUMDB_QUERY_DATA_H
#pragma once
#include <optional>
#include "query/var_id.h"
#include "graph_models/quad_model/quad_model.h"
#include "system/path_manager.h"

inline std::optional<uint64_t> query_property(uint64_t obj_id, uint64_t key_id)  {
    // Search B+Tree for *values* given <obj,key>
    std::array<uint64_t, 3> min_prop_ids {};
    std::array<uint64_t, 3> max_prop_ids {};
    min_prop_ids[0] = obj_id;
    max_prop_ids[0] = obj_id;
    min_prop_ids[1] = key_id;
    max_prop_ids[1] = key_id;
    min_prop_ids[2] = 0;
    max_prop_ids[2] = UINT64_MAX;
    auto prop_iter = quad_model.object_key_value->get_range(
            &get_query_ctx().thread_info.interruption_requested,
            Record<3>(min_prop_ids),
            Record<3>(max_prop_ids));
    auto prop_record = prop_iter.next();
    if (prop_record == nullptr){
        return std::nullopt;
    }
    else {
        auto record_value_id = (*prop_record)[2];
        return record_value_id;
    }
}

inline BptIter<2> query_label(uint64_t obj_id) {
    std::array<uint64_t ,2> min_prop_ids{};
    std::array<uint64_t, 2> max_prop_ids{};
    max_prop_ids[0] = obj_id;
    min_prop_ids[0] = obj_id;
    max_prop_ids[1] = UINT64_MAX,
            min_prop_ids[1] = 0;
    auto prop_iter = quad_model.node_label->get_range(
            &get_query_ctx().thread_info.interruption_requested,
            Record<2>(min_prop_ids),
            Record<2>(max_prop_ids));
    return prop_iter;
}

inline bool match_label(uint64_t obj_id, uint64_t label_id) {
    auto labels_iter = query_label(obj_id);
    auto label_record = labels_iter.next();
    while(label_record != nullptr){
        if ((*label_record)[1] == label_id) {
            return true;
        }
        else {
            label_record = labels_iter.next();
        }
    }
    return false;
}
#endif //MILLENNIUMDB_QUERY_DATA_H
