#pragma once

#include "query/executor/binding_iter/scan_ranges/scan_range.h"
#include "query/query_context.h"

enum class propertyType : uint64_t {
    TYPE_NULL = 1 << 4, // 10000
    TYPE_STRING = 1 << 3, // 01000
    TYPE_INTEGER = 1 << 2, // 00100
    TYPE_BOOL = 1 << 1, // 00010
    TYPE_FLOAT = 1 << 0, // 00001
};

class RangeType : public ScanRange {
private:
    VarId var;
    uint64_t type_bitmap;

public:
    RangeType(VarId var, uint64_t type_bitmap) :
        var(var),
        type_bitmap(type_bitmap)
    { }

    uint64_t get_min(Binding&) override
    {
        if (type_bitmap & static_cast<uint64_t>(propertyType::TYPE_BOOL)) {
            return 0x70'00000000000000UL | 0UL;
        }
        if (type_bitmap & static_cast<uint8_t>(propertyType::TYPE_INTEGER)) {
            return 0x50'00000000000000UL;
        }
        if (type_bitmap & static_cast<uint8_t>(propertyType::TYPE_FLOAT)) {
            return 0x54'00000000000000UL;
        }
        if (type_bitmap & static_cast<uint8_t>(propertyType::TYPE_STRING)) {
            return 0x40'00000000000000UL;
        } else {
            return 0;
        }
    }

    uint64_t get_max(Binding&) override
    {
        if (type_bitmap & static_cast<uint64_t>(propertyType::TYPE_BOOL)) {
            return 0x70'00000000000000UL | 1UL;
        }
        if (type_bitmap & static_cast<uint8_t>(propertyType::TYPE_INTEGER)) {
            return 0x56'00000000000000UL;
        }
        if (type_bitmap & static_cast<uint8_t>(propertyType::TYPE_FLOAT)) {
            return 0x5E'00000000000000UL;
        }
        if (type_bitmap & static_cast<uint8_t>(propertyType::TYPE_STRING)) {
            return 0x4E'00000000000000UL;
        } else {
            return 0;
        }
    }

    void print(std::ostream& os) const override
    {
        os << type_bitmap;
    }

    void try_assign(Binding& binding, ObjectId obj_id) override
    {
        binding.add(var, obj_id);
    }
};