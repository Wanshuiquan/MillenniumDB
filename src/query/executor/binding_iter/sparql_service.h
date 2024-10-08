#pragma once

#include <cstdint>
#include <map>

#include "query/executor/binding_iter.h"
#include "network/sparql/service/response_parser.h"

class SparqlService : public BindingIter {
public:
    SparqlService(
        bool                             silent,
        std::string&&                    query,
        std::string&&                    prefixes,
        std::variant<VarId, std::string> var_or_iri,
        std::set<VarId>                  _scope_vars,
        std::set<VarId>                  _fixed_vars,
        std::set<VarId>                  fixed_join_vars
    ) :
        scope_vars      (std::move(_scope_vars)),
        fixed_vars      (std::move(_fixed_vars)),
        fixed_join_vars (std::move(fixed_join_vars)),
        silent          (silent),
        response_parser (ResponseParser(
            std::move(query),
            std::move(prefixes),
            var_or_iri,
            scope_vars,
            fixed_vars)
        ) { }

    void analyze(std::ostream& os, int indent = 0) const override;
    void begin(Binding& parent_binding) override;
    bool next() override;
    void reset() override;
    void assign_nulls() override;

private:
    Binding* parent_binding;

    // Variables that are in scope after evaluating this service
    std::set<VarId> scope_vars;
    // Variables fixed by parent
    std::set<VarId> fixed_vars;
    // Variables fixed by parent that are involved in joins with other operators
    std::set<VarId> fixed_join_vars;

    bool silent;
    bool failed; // Used when the SILENT token is present
    bool first_next; // Try to consume API in the first next

    ResponseParser response_parser;

    uint64_t network_requests = 0;
    uint64_t result_count = 0;
    uint64_t executions = 0;
};
