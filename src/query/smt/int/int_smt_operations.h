//
// Created by heyang-li on 4/27/26.
//

#ifndef MILLENNIUMDB_INT_SMT_OPERATIONS_H
#define MILLENNIUMDB_INT_SMT_OPERATIONS_H
#include <cmath>
#include <limits>
#include <variant>
#include <iostream>
#include "graph_models/inliner.h"
#include "graph_models/quad_model/conversions.h"
#include "graph_models/quad_model/quad_object_id.h"


using ResultInt = std::variant<int64_t, std::string, bool>;
ResultInt inline decode_mask_int(ObjectId oid) {
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
            return i;
    }
    case ObjectId::MASK_FLOAT: {
            const double value = Common::Conversions::unpack_float(oid);
            if (!std::isfinite(value)
                    || std::trunc(value) != value
                    || value < static_cast<double>(std::numeric_limits<int64_t>::min())
                    || value > static_cast<double>(std::numeric_limits<int64_t>::max())) {
                throw std::logic_error("Non-integral float in integer data-test attribute: "
                                       + std::to_string(value));
            }
            return static_cast<int64_t>(value);
    }
    case ObjectId::MASK_BOOL: {
            return  unmasked_id != 0;
    }

    default:
        throw std::logic_error("Unmanaged mask in ReturnExecutor print: "
                               + std::to_string(mask));
    }
}
#endif //MILLENNIUMDB_INT_SMT_OPERATIONS_H
