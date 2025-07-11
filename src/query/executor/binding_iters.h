#include "query/executor/binding_iter/aggregation.h"                // IWYU pragma: keep
#include "query/executor/binding_iter/bind.h"                       // IWYU pragma: keep
#include "query/executor/binding_iter/cross_product.h"              // IWYU pragma: keep
#include "query/executor/binding_iter/distinct_hash.h"              // IWYU pragma: keep
#include "query/executor/binding_iter/edge_table_lookup.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/empty_binding_iter.h"         // IWYU pragma: keep
#include "query/executor/binding_iter/expr_evaluator.h"             // IWYU pragma: keep
#include "query/executor/binding_iter/filter.h"                     // IWYU pragma: keep
#include "query/executor/binding_iter/index_left_outer_join.h"      // IWYU pragma: keep
#include "query/executor/binding_iter/index_nested_loop_join.h"     // IWYU pragma: keep
#include "query/executor/binding_iter/index_scan.h"                 // IWYU pragma: keep
#include "query/executor/binding_iter/leapfrog_join.h"              // IWYU pragma: keep
#include "query/executor/binding_iter/nested_loop_anti_join.h"      // IWYU pragma: keep
#include "query/executor/binding_iter/nested_loop_join.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/nested_loop_left_join.h"      // IWYU pragma: keep
#include "query/executor/binding_iter/nested_loop_semi_join.h"      // IWYU pragma: keep
#include "query/executor/binding_iter/no_free_variable_minus.h"     // IWYU pragma: keep
#include "query/executor/binding_iter/object_enum.h"                // IWYU pragma: keep
#include "query/executor/binding_iter/order_by.h"                   // IWYU pragma: keep
#include "query/executor/binding_iter/sequence.h"                   // IWYU pragma: keep
#include "query/executor/binding_iter/set_repeated_variable.h"      // IWYU pragma: keep
#include "query/executor/binding_iter/set_constants.h"              // IWYU pragma: keep
#include "query/executor/binding_iter/set_end_boundary_variable.h"  // IWYU pragma: keep
#include "query/executor/binding_iter/set_labels.h"                 // IWYU pragma: keep
#include "query/executor/binding_iter/set_start_boundary_variable.h"// IWYU pragma: keep
#include "query/executor/binding_iter/single_result_binding_iter.h" // IWYU pragma: keep
#include "query/executor/binding_iter/slice.h"                      // IWYU pragma: keep
#include "query/executor/binding_iter/sparql_service.h"             // IWYU pragma: keep
#include "query/executor/binding_iter/sub_select.h"                 // IWYU pragma: keep
#include "query/executor/binding_iter/text_search_index_scan.h"     // IWYU pragma: keep
#include "query/executor/binding_iter/union.h"                      // IWYU pragma: keep
#include "query/executor/binding_iter/values.h"                     // IWYU pragma: keep


#include "query/executor/binding_iter/hash_join/bgp/hybrid/join.h"             // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/bgp/hybrid/join_1_var.h"       // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/bgp/in_memory/join.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/bgp/in_memory/join_1_var.h"    // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/hybrid/anti_join.h"    // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/hybrid/join.h"         // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/hybrid/left_join.h"    // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/hybrid/semi_join.h"    // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/in_memory/anti_join.h" // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/in_memory/join.h"      // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/in_memory/left_join.h" // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/generic/in_memory/semi_join.h" // IWYU pragma: keep
#include "query/executor/binding_iter/hash_join/materialize_iter.h"            // IWYU pragma: keep

#include "query/executor/binding_iter/paths/all_shortest_simple/bfs_check.h" // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_shortest_simple/bfs_enum.h"  // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_shortest_trails/bfs_check.h" // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_shortest_trails/bfs_enum.h"  // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_shortest_walks/bfs_check.h"  // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_shortest_walks/bfs_enum.h"   // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_simple/bfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_simple/bfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_simple/dfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_simple/dfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_trails/bfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_trails/bfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_trails/dfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/all_trails/dfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_simple/bfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_simple/bfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_simple/dfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_simple/dfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_trails/bfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_trails/bfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_trails/dfs_check.h"          // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_trails/dfs_enum.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_walks/bfs_check.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_walks/bfs_enum.h"            // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_walks/dfs_check.h"           // IWYU pragma: keep
#include "query/executor/binding_iter/paths/any_walks/dfs_enum.h"            // IWYU pragma: keep
#include "query/executor/binding_iter/paths/experimental/all_shortest_walks_count/bfs_check.h" // IWYU pragma: keep
#include "query/executor/binding_iter/paths/experimental/all_shortest_walks_count/bfs_enum.h" // IWYU pragma: keep
#include "query/executor/binding_iter/paths/experimental/bfs_rdpq_check.h" // IWYU pragma: keep
#include "query/executor/binding_iter/paths/experimental/bfs_rdpq_enum.h"  // IWYU pragma: keep
#include "query/executor/binding_iter/paths/experimental/dijkstra_check.h" // IWYU pragma: keep
#include "query/executor/binding_iter/paths/experimental/dijkstra_enum.h"  // IWYU pragma: keep
#include "query/executor/binding_iter/paths/unfixed_composite.h"           // IWYU pragma: keep

#include "query/executor/binding_iter/paths/data_test/bfs_check.h"
#include "query/executor/binding_iter/paths/data_test/bfs_enum.h"
#include "query/executor/binding_iter/paths/data_test/experimental/naive_bfs_check.h"
#include "query/executor/binding_iter/paths/data_test/experimental/naive_bfs_enum.h"