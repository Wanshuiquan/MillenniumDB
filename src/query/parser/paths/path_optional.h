#pragma once

#include "query/parser/paths/regular_path_expr.h"

class PathOptional : public RegularPathExpr {
public:
    std::unique_ptr<RegularPathExpr> path;

    PathOptional(std::unique_ptr<RegularPathExpr> path) : path(std::move(path)) { }

    PathType type() const override {
        return PathType::PATH_OPTIONAL;
    }

    std::unique_ptr<RegularPathExpr> clone() const override {
        return std::make_unique<PathOptional>(path->clone());
    }
    std::set<VarId> get_var() const
    {
        return path->get_var();
    }

    std::set<std::tuple<std::string, ObjectId>> collect_attr() const override{
        return path -> collect_attr();
    }

    std::set<VarId> collect_para() const override{
        return path -> collect_para();
    }
    std::string to_string() const override {
        std::string res = "(";
        res.append(path->to_string());
        res.append(")?");
        return res;
    }

    std::ostream& print_to_ostream(std::ostream& os, int indent = 0) const override {
        os << std::string(indent, ' ');
        os << "PathOptional()\n";
        path->print_to_ostream(os, indent + 2);
        return os;
    }

    bool nullable() const override {
        return true;
    }

    std::unique_ptr<RegularPathExpr> invert() const override {
        return std::make_unique<PathOptional>(path->invert());
    }

    RPQ_NFA get_rpq_base_automaton() const override {
        auto automaton = path->get_rpq_base_automaton();
        // Make start state a end state
        automaton.end_states.insert(automaton.get_start());
        return automaton;
    }
    SMTAutomaton get_smt_base_automaton() const override{
        auto automaton = path->get_smt_base_automaton();
        // Make start state a end state
        automaton.end_states.insert(automaton.get_start());
        return automaton;
    }
    RDPQAutomaton get_rdpq_base_automaton() const override {
        auto automaton = path->get_rdpq_base_automaton();

        // Remove transitions from start to end states (to avoid unnecessary transitions)
        size_t s_transition_n = 0;
        while (s_transition_n < automaton.from_to_connections[automaton.get_start()].size()) {
            auto s_t = automaton.from_to_connections[automaton.get_start()][s_transition_n];
            if (automaton.end_states.find(s_t.to) != automaton.end_states.end()) {
                // Delete unnecessary transition to end state
                automaton.from_to_connections[automaton.get_start()].erase(
                    automaton.from_to_connections[automaton.get_start()].begin() + s_transition_n);
            } else {
                s_transition_n++;
            }
        }
        for (auto end_state = automaton.end_states.begin(); end_state != automaton.end_states.end();) {
            size_t transition_n = 0;
            while (transition_n < automaton.to_from_connections[*end_state].size()) {
                auto t = automaton.to_from_connections[*end_state][transition_n];
                if (t.from == automaton.get_start()) {
                    // Delete unnecessary transition from start state
                    automaton.to_from_connections[*end_state].erase(
                        automaton.to_from_connections[*end_state].begin() + transition_n);
                } else {
                    transition_n++;
                }
            }

            // End state is no longer reachable, remove it
            if (!automaton.to_from_connections[*end_state].size()) {
                end_state = automaton.end_states.erase(end_state);
            } else {
                end_state++;
            }
        }

        // Add new state to allow skipping the pattern
        auto new_state = automaton.get_total_states();
        automaton.add_transition(RDPQTransition::make_data_transition(automaton.get_start(), new_state));
        automaton.end_states.insert(new_state);
        return automaton;
    }
};
