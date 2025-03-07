#include "graph_models/common/datatypes/datetime.h"

#include <algorithm>
#include <iostream>
#include <string>
#include <tuple>
#include <vector>


int compare_date_time() {
    std::tuple<std::string, std::string, int64_t, bool> tests[] = {
        {"-2011-11-11T11:11:11",  "2011-11-11T11:11:11", -1, false},
        { "2011-11-11T11:11:11",  "2011-11-11T11:11:11",  0, false},
        { "2011-11-11T11:11:11", "-2011-11-11T11:11:11",  1, false},

        {"2011-11-11T11:11:10", "2011-11-11T11:11:11", -1, false},
        {"2011-11-11T11:10:11", "2011-11-11T11:11:11", -1, false},
        {"2011-11-11T10:11:11", "2011-11-11T11:11:11", -1, false},
        {"2011-11-10T11:11:11", "2011-11-11T11:11:11", -1, false},
        {"2011-10-11T11:11:11", "2011-11-11T11:11:11", -1, false},
        {"2010-11-11T11:11:11", "2011-11-11T11:11:11", -1, false},

        {"2011-11-11T11:11:11", "2011-11-11T11:11:10", 1, false},
        {"2011-11-11T11:11:11", "2011-11-11T11:10:11", 1, false},
        {"2011-11-11T11:11:11", "2011-11-11T10:11:11", 1, false},
        {"2011-11-11T11:11:11", "2011-11-10T11:11:11", 1, false},
        {"2011-11-11T11:11:11", "2011-10-11T11:11:11", 1, false},
        {"2011-11-11T11:11:11", "2010-11-11T11:11:11", 1, false},

        {"-2011-11-11T11:11:10", "-2011-11-11T11:11:11", -1, false},
        {"-2011-11-11T11:10:11", "-2011-11-11T11:11:11", -1, false},
        {"-2011-11-11T10:11:11", "-2011-11-11T11:11:11", -1, false},
        {"-2011-11-10T11:11:11", "-2011-11-11T11:11:11", -1, false},
        {"-2011-10-11T11:11:11", "-2011-11-11T11:11:11", -1, false},
        {"-2010-11-11T11:11:11", "-2011-11-11T11:11:11",  1, false},

        {"-2011-11-11T11:11:11", "-2011-11-11T11:11:10",  1, false},
        {"-2011-11-11T11:11:11", "-2011-11-11T11:10:11",  1, false},
        {"-2011-11-11T11:11:11", "-2011-11-11T10:11:11",  1, false},
        {"-2011-11-11T11:11:11", "-2011-11-10T11:11:11",  1, false},
        {"-2011-11-11T11:11:11", "-2011-10-11T11:11:11",  1, false},
        {"-2011-11-11T11:11:11", "-2010-11-11T11:11:11", -1, false},

        // Mixing timezone and no timezone
        {"-2011-11-11T11:11:11Z",  "2011-11-11T11:11:11", -1, false},
        { "2011-11-11T11:11:11Z",  "2011-11-11T11:11:11",  0, true},
        {"-2011-11-11T11:11:11Z", "-2011-11-11T11:11:11",  0, true},
        { "2011-11-11T11:11:11Z", "-2011-11-11T11:11:11",  1, false},

        {"-2011-11-11T11:11:11",  "2011-11-11T11:11:11Z", -1, false},
        { "2011-11-11T11:11:11",  "2011-11-11T11:11:11Z",  0, true},
        {"-2011-11-11T11:11:11", "-2011-11-11T11:11:11Z",  0, true},
        { "2011-11-11T11:11:11", "-2011-11-11T11:11:11Z",  1, false},

        // Z timezone should be the same as +00:00
        {"-2011-11-11T11:11:11Z",  "2011-11-11T11:11:11+00:00", -1, false},
        { "2011-11-11T11:11:11Z",  "2011-11-11T11:11:11+00:00",  0, false},
        {"-2011-11-11T11:11:11Z", "-2011-11-11T11:11:11+00:00",  0, false},
        { "2011-11-11T11:11:11Z", "-2011-11-11T11:11:11+00:00",  1, false},

        {"-2011-11-11T11:11:11+00:00",  "2011-11-11T11:11:11Z", -1, false},
        { "2011-11-11T11:11:11+00:00",  "2011-11-11T11:11:11Z",  0, false},
        {"-2011-11-11T11:11:11+00:00", "-2011-11-11T11:11:11Z",  0, false},
        { "2011-11-11T11:11:11+00:00", "-2011-11-11T11:11:11Z",  1, false},

        // Z timezone should be the same as -00:00
        {"-2011-11-11T11:11:11Z",  "2011-11-11T11:11:11-00:00", -1, false},
        { "2011-11-11T11:11:11Z",  "2011-11-11T11:11:11-00:00",  0, false},
        {"-2011-11-11T11:11:11Z", "-2011-11-11T11:11:11-00:00",  0, false},
        { "2011-11-11T11:11:11Z", "-2011-11-11T11:11:11-00:00",  1, false},

        {"-2011-11-11T11:11:11-00:00",  "2011-11-11T11:11:11Z", -1, false},
        { "2011-11-11T11:11:11-00:00",  "2011-11-11T11:11:11Z",  0, false},
        {"-2011-11-11T11:11:11-00:00", "-2011-11-11T11:11:11Z",  0, false},
        { "2011-11-11T11:11:11-00:00", "-2011-11-11T11:11:11Z",  1, false},

        // Timezone should be taken into account
        { "2011-11-11T15:11:11-05:00", "2011-11-11T20:11:11Z",      0, false},
        { "2011-11-11T15:11:11-05:00", "2011-11-11T20:11:11+00:00", 0, false},
        { "2011-11-11T15:11:11-05:00", "2011-11-11T20:11:11-00:00", 0, false},

        { "2011-11-11T15:11:11-05:00", "2011-11-11T17:11:11-03:00",  0, false},
        { "2011-11-11T15:11:11-05:00", "2011-11-11T22:11:11+02:00",  0, false},
        { "2011-11-11T15:11:11-05:00", "2011-11-11T22:11:11+01:00", -1, false},
        { "2011-11-11T15:11:11-05:00", "2011-11-11T17:11:11-02:00",  1, false},

        // +-14 error range
        { "2010-10-10T10:10:10", "2010-10-10T10:10:09+14:00",  1, false},
        { "2010-10-10T10:10:10", "2010-10-10T10:10:10+14:00",  0, true},
        { "2010-10-10T10:10:10", "2010-10-10T10:10:10+00:00",  0, true},
        { "2010-10-10T10:10:10", "2010-10-10T10:10:10-14:00",  0, true},
        { "2010-10-10T10:10:10", "2010-10-10T10:10:11-14:00", -1, false},

        { "2010-10-10T10:10:10", "2010-10-09T20:10:09Z",  1, false},
        { "2010-10-10T10:10:10", "2010-10-09T20:10:10Z",  0, true},
        { "2010-10-10T10:10:10", "2010-10-10T10:10:10Z",  0, true},
        { "2010-10-10T10:10:10", "2010-10-11T00:10:10Z",  0, true},
        { "2010-10-10T10:10:10", "2010-10-11T00:10:11Z", -1, false},

        // Low precision
        { "16383-10-10T10:10:10", "16383-10-10T10:10:11", -1, false}, // Normal precision

        { "16383-10-10T10:10:10", "16384-10-10T10:10:10", -1, false}, // Normal precision, low precision
        { "16384-10-10T10:10:10", "16383-10-10T10:10:10",  1, false}, // low precision, normal precision

        { "2010-10-10T10:10:10", "999999999-10-10T10:10:10",  -1, false}, // Normal precision, low precision

        { "999999999-10-10T10:10:10",      "2010-10-10T10:10:10",   1, false}, // Low precision, normal precision
        { "999999999-10-10T10:10:10", "999999998-10-10T10:10:10",   1, false}, // Low precision, low precision
        { "999999998-10-10T10:10:10", "999999999-10-10T10:10:10",  -1, false}, // Low precision, low precision
        { "999999999-10-10T10:10:10", "999999999-10-10T10:10:10",   0, false}, // Low precision, low precision
        { "999999998-10-10T10:10:10", "999999998-10-10T10:10:10",   0, false}, // Low precision, low precision

        { "-999999999-10-10T10:10:10",      "-2010-10-10T10:10:10",  -1, false}, // Low precision, normal precision
        { "-999999999-10-10T10:10:10", "-999999998-10-10T10:10:10",  -1, false}, // Low precision, low precision
        { "-999999998-10-10T10:10:10", "-999999999-10-10T10:10:10",   1, false}, // Low precision, low precision
        { "-999999999-10-10T10:10:10", "-999999999-10-10T10:10:10",   0, false}, // Low precision, low precision
        { "-999999998-10-10T10:10:10", "-999999998-10-10T10:10:10",   0, false}, // Low precision, low precision

        { "999999999-10-10T10:10:10",      "-2010-10-10T10:10:10", 1, false}, // Low precision, normal precision
        { "999999999-10-10T10:10:10", "-999999998-10-10T10:10:10", 1, false}, // Low precision, low precision
        { "999999998-10-10T10:10:10", "-999999999-10-10T10:10:10", 1, false}, // Low precision, low precision
        { "999999999-10-10T10:10:10", "-999999999-10-10T10:10:10", 1, false}, // Low precision, low precision
        { "999999998-10-10T10:10:10", "-999999998-10-10T10:10:10", 1, false}, // Low precision, low precision

        { "-999999999-10-10T10:10:10",      "2010-10-10T10:10:10", -1, false}, // Low precision, normal precision
        { "-999999999-10-10T10:10:10", "999999998-10-10T10:10:10", -1, false}, // Low precision, low precision
        { "-999999998-10-10T10:10:10", "999999999-10-10T10:10:10", -1, false}, // Low precision, low precision
        { "-999999999-10-10T10:10:10", "999999999-10-10T10:10:10", -1, false}, // Low precision, low precision
        { "-999999998-10-10T10:10:10", "999999998-10-10T10:10:10", -1, false}, // Low precision, low precision

        { "999999998-10-10T10:10:10", "899999998-10-10T10:10:10",  1, false}, // Low precision, low precision
        { "899999998-10-10T10:10:10", "999999998-10-10T10:10:10", -1, false}, // Low precision, low precision

        { "13510798882111488-10-10T10:10:10",  "4503599627370496-10-10T10:10:10",  1, false}, // Low precision, low precision
        {  "4503599627370496-10-10T10:10:10", "13510798882111488-10-10T10:10:10", -1, false}, // Low precision, low precision

        { "16384-10-10T10:10:10", "16384-10-10T10:10:11",  0, false}, // Low precision, years only
        { "16384-10-10T10:10:10", "16385-10-10T10:10:11", -1, false}, // Low precision, years only
        { "16385-10-10T10:10:10", "16385-10-10T10:10:11",  0, false}, // Low precision, years only
        { "16385-10-10T10:10:10", "16384-10-10T10:10:11",  1, false}, // Low precision, years only
    };

    for (auto& [lhs, rhs, expected_result, expected_error] : tests) {
        auto lhs_dt = DateTime(DateTime::from_dateTime(lhs));
        auto rhs_dt = DateTime(DateTime::from_dateTime(rhs));
        bool error;
        int64_t result = lhs_dt.compare<DateTimeComparisonMode::Strict>(rhs_dt, &error);
        result = std::min(std::max(static_cast<int64_t>(-1), result), static_cast<int64_t>(1)); // Turn into -1,0,1;
        if (expected_error && !error) {
            std::cerr << lhs << " compare " << rhs << ": expected error\n";
            return 1;
        } else if (!expected_error && error) {
            std::cerr << lhs << " compare " << rhs << ": did not expect error\n";
            return 1;
        } else if (!expected_error && result != expected_result) {
            std::cerr << lhs << " compare " << rhs << ": expected " << expected_result << ", got " << result << "\n";
            return 1;
        }
    }
    return 0;
}


typedef int TestFunction();


int main() {
    std::vector<TestFunction*> tests;

    tests.push_back(&compare_date_time);

    for (auto& test_func : tests) {
        if (test_func()) {
            return 1;
        }
    }
    return 0;
}
