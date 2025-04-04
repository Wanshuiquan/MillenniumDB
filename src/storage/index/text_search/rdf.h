
#pragma once

#include "storage/index/text_search/model_funcs.h"

namespace TextSearch { namespace RDF {

IndexPredicateFuncType index_predicate;
IndexSingleFuncType index_single;
RemoveSingleFuncType remove_single;
ObjectIdToStringFuncType oid_to_string;

}} // namespace TextSearch::RDF
