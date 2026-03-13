//
// Created by lhy on 11/11/24.
//

#ifndef MILLENNIUMDB_SMT_OPERATIONS_H
#define MILLENNIUMDB_SMT_OPERATIONS_H
#pragma once
#include <variant>
#include <iostream>
#include "graph_models/inliner.h"
#include "graph_models/quad_model/conversions.h"
#include "graph_models/quad_model/quad_object_id.h"



using Result = std::variant<double, std::string, bool>;
Result inline decode_mask(ObjectId oid) {
    const auto mask        = oid.id & ObjectId::TYPE_MASK;
    const auto unmasked_id = oid.id & ObjectId::VALUE_MASK;
    std::stringstream escaped_os;
    std::stringstream os;
    switch (mask) {
        case ObjectId::MASK_NULL: {
            return "null";
        }

        case ObjectId::MASK_STRING_SIMPLE_INLINED: {
            Inliner::print_string_inlined<7>(escaped_os, unmasked_id);
            auto val = escaped_os.str();
            return val;
        }
        case ObjectId::MASK_STRING_SIMPLE_EXTERN: {
            string_manager.print(escaped_os, unmasked_id);
            auto val = escaped_os.str();
            return val;
        }
        case ObjectId::MASK_STRING_SIMPLE_TMP: {
            tmp_manager.print_str(escaped_os, unmasked_id);
            auto val = escaped_os.str();
            return val;

        }
        case ObjectId::MASK_NEGATIVE_INT:
        case ObjectId::MASK_POSITIVE_INT: {
            int64_t i = Common::Conversions::unpack_int(oid);
            return (double_t) i;
        }
        case ObjectId::MASK_FLOAT: {
            double_t f = Common::Conversions::unpack_float(oid);
            return f;
        }
        case ObjectId::MASK_BOOL: {
            return  unmasked_id != 0;
        }

        default:
            throw std::logic_error("Unmanaged mask in ReturnExecutor print: "
                                   + std::to_string(mask));
    }
}

#endif //MILLENNIUMDB_SMT_OPERATIONS_H
