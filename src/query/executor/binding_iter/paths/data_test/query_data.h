//
// Created by lhy on 9/19/24.
//

#ifndef MILLENNIUMDB_QUERY_DATA_H
#define MILLENNIUMDB_QUERY_DATA_H
#pragma once
#include <cctype>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include "graph_models/quad_model/conversions.h"
#include "graph_models/quad_model/quad_model.h"
#include "system/path_manager.h"

inline std::optional<uint64_t> query_inline_property(uint64_t obj_id, uint64_t key_id)  {
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

inline std::optional<uint64_t> query_property(uint64_t obj_id, uint64_t key_id)  {
    if (auto inline_value = query_inline_property(obj_id, key_id); inline_value.has_value()) {
        return inline_value;
    }

    static const uint64_t type_key_id = QuadObjectId::get_string("type").id;
    static const uint64_t value_tag_id = QuadObjectId::get_string("value").id;
    const auto key_lexical = MQL::Conversions::to_lexical_str(ObjectId(key_id));

    std::array<uint64_t, 4> min_edge_ids {};
    std::array<uint64_t, 4> max_edge_ids {};
    min_edge_ids[0] = obj_id;
    max_edge_ids[0] = obj_id;
    min_edge_ids[1] = 0;
    max_edge_ids[1] = UINT64_MAX;
    min_edge_ids[2] = 0;
    max_edge_ids[2] = UINT64_MAX;
    min_edge_ids[3] = 0;
    max_edge_ids[3] = UINT64_MAX;

    auto edge_iter = quad_model.from_to_type_edge->get_range(
            &get_query_ctx().thread_info.interruption_requested,
            Record<4>(min_edge_ids),
            Record<4>(max_edge_ids));

    auto edge_record = edge_iter.next();
    while (edge_record != nullptr) {
        const uint64_t target_id = (*edge_record)[1];
        const uint64_t type_id = (*edge_record)[2];
        const uint64_t edge_id = (*edge_record)[3];

        if (type_id != key_id
            && MQL::Conversions::to_lexical_str(ObjectId(type_id)) != key_lexical)
        {
            edge_record = edge_iter.next();
            continue;
        }

        auto edge_type = query_inline_property(edge_id, type_key_id);
        if (edge_type.has_value() && edge_type.value() == value_tag_id) {
            return target_id;
        }

        edge_record = edge_iter.next();
    }

    return std::nullopt;
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

inline bool data_test_is_identifier_char(unsigned char ch) {
    return std::isalnum(ch) || ch == '_' || ch == '?';
}

inline bool data_test_formula_mentions_attr(std::string_view formula, std::string_view attr_name) {
    bool in_string = false;

    for (size_t i = 0; i < formula.size(); ++i) {
        if (formula[i] == '"') {
            in_string = !in_string;
            continue;
        }

        if (in_string) {
            continue;
        }

        if (formula.compare(i, attr_name.size(), attr_name) != 0) {
            continue;
        }

        const bool left_boundary =
            (i == 0) || !data_test_is_identifier_char(static_cast<unsigned char>(formula[i - 1]));
        const size_t end = i + attr_name.size();
        const bool right_boundary =
            (end == formula.size()) || !data_test_is_identifier_char(static_cast<unsigned char>(formula[end]));

        if (left_boundary && right_boundary) {
            return true;
        }
    }

    return false;
}

// A missing property makes the current data-test transition unsatisfied. Keep
// this check before parsing the SMT formula so absent attributes cannot become
// undeclared Z3 constants. We only require attributes that are referenced by
// the current transition formula, not every attribute that appears somewhere in
// the whole path expression.
template <typename... AttributeMaps>
inline bool data_test_formula_attributes_complete(
        std::string_view formula,
        const std::set<std::tuple<std::string, ObjectId>>& attributes,
        const AttributeMaps&... maps) {
    auto has_attr_value = [&](const auto& attr) {
        return ((maps.find(attr) != maps.end()) || ...);
    };

    for (const auto& attr : attributes) {
        if (!data_test_formula_mentions_attr(formula, std::get<0>(attr))) {
            continue;
        }

        if (!has_attr_value(attr)) {
            return false;
        }
    }

    return true;
}
#endif //MILLENNIUMDB_QUERY_DATA_H
