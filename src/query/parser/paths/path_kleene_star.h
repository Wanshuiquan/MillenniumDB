#pragma once

#include <algorithm>

#include "query/parser/paths/regular_path_expr.h"
#include "query/parser/paths/denull_path.h"

class PathKleeneStar : public RegularPathExpr {
public:
    std::unique_ptr<RegularPathExpr> path;

    PathKleeneStar(std::unique_ptr<RegularPathExpr> path) :
        path (PathDenull::denull(std::move(path))) { }

    PathKleeneStar(const PathKleeneStar& other) :
        path (other.path->clone()) { }

    std::unique_ptr<RegularPathExpr> clone() const override {
        return std::make_unique<PathKleeneStar>(*this);
    }

    PathType type() const override {
        return PathType::PATH_KLEENE_STAR;
    }
    std::set<VarId> get_var()const
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
        res.append(")*");
        return res;
    }

    std::ostream& print_to_ostream(std::ostream& os, int indent = 0) const override {
        os << std::string(indent, ' ');
        os << "PathKleeneStar()\n";
        path->print_to_ostream(os, indent + 2);
        return os;
    }

    bool nullable() const override {
        return true;
    }

    RPQ_NFA get_rpq_base_automaton() const override {
        auto path_automaton = path->get_rpq_base_automaton();

        // Connects all end states to start state
        for (const auto& end_state : path_automaton.end_states) {
            path_automaton.add_epsilon_transition(end_state, path_automaton.get_start());
        }

        // Makes start state final
        path_automaton.end_states.insert(path_automaton.get_start());
        return path_automaton;
    }
    SMTAutomaton get_smt_base_automaton() const override {
        auto path_automaton = path->get_smt_base_automaton();

        // Connects all end states to start state
        for (const auto& end_state : path_automaton.end_states) {
            path_automaton.add_epsilon_transition(end_state, path_automaton.get_start());
        }

        // Makes start state final
        path_automaton.end_states.insert(path_automaton.get_start());
        return path_automaton;
    }
    RDPQAutomaton get_rdpq_base_automaton() const override {
        auto path_automaton = path->get_rdpq_base_automaton();

        // Remove transitions from start to end states (to avoid unnecessary transitions)
        size_t s_transition_n = 0;
        while (s_transition_n < path_automaton.from_to_connections[path_automaton.get_start()].size()) {
            auto s_t = path_automaton.from_to_connections[path_automaton.get_start()][s_transition_n];
            if (path_automaton.end_states.find(s_t.to) != path_automaton.end_states.end()) {
                // Delete unnecessary transition to end state
                path_automaton.from_to_connections[path_automaton.get_start()].erase(
                    path_automaton.from_to_connections[path_automaton.get_start()].begin() + s_transition_n);
            } else {
                s_transition_n++;
            }
        }
        for (auto end_state = path_automaton.end_states.begin(); end_state != path_automaton.end_states.end();) {
            size_t transition_n = 0;
            while (transition_n < path_automaton.to_from_connections[*end_state].size()) {
                auto t = path_automaton.to_from_connections[*end_state][transition_n];
                if (t.from == path_automaton.get_start()) {
                    // Delete unnecessary transition from start state
                    path_automaton.to_from_connections[*end_state].erase(
                        path_automaton.to_from_connections[*end_state].begin() + transition_n);
                } else {
                    transition_n++;
                }
            }

            // End state is no longer reachable, remove it
            if (!path_automaton.to_from_connections[*end_state].size()) {
                end_state = path_automaton.end_states.erase(end_state);
            } else {
                end_state++;
            }
        }

        // Add new state to allow skipping/stopping the pattern
        auto new_state = path_automaton.get_total_states();
        path_automaton.add_transition(RDPQTransition::make_data_transition(path_automaton.get_start(), new_state));

        // Iterate over current end states & get all states that have transitions towards an end state
        std::set<uint_fast32_t> states;
        for (auto& end_state : path_automaton.end_states) {
            for (auto& t_in : path_automaton.to_from_connections[end_state]) {
                states.insert(t_in.from);
            }
            path_automaton.to_from_connections[end_state].clear();
        }

        // Merge transitions 'to' end states with transitions 'from' start state (kleene loop)
        for (auto& state : states) {
            size_t transition_n = 0;
            while (transition_n < path_automaton.from_to_connections[state].size()) {
                auto t = path_automaton.from_to_connections[state][transition_n];
                if (path_automaton.end_states.find(t.to) != path_automaton.end_states.end()) {
                    // Merge transition for the loop
                    for (auto& s : path_automaton.from_to_connections[path_automaton.get_start()]) {
                        std::vector<std::tuple<Operators, ObjectId, ObjectId>> data_checks;
                        for (size_t i = 0; i < t.property_checks.size(); i++) {
                            data_checks.push_back(t.property_checks[i]);
                        }
                        for (size_t i = 0; i < s.property_checks.size(); i++) {
                            data_checks.push_back(s.property_checks[i]);
                        }

                        // Remove duplicates for data check
                        std::sort(data_checks.begin(), data_checks.end());
                        data_checks.erase(unique(data_checks.begin(), data_checks.end()), data_checks.end());

                        // Add new 'loop' transition
                        path_automaton.add_transition(RDPQTransition::make_data_transition(t.from, s.to, std::move(data_checks)));
                    }

                    // Delete old transition to end state
                    path_automaton.from_to_connections[state].erase(
                        path_automaton.from_to_connections[state].begin() + transition_n);
                } else {
                    transition_n++;
                }
            }
        }

        // New state is now the only end state
        path_automaton.end_states.clear();
        path_automaton.end_states.insert(new_state);
        return path_automaton;
    }

    std::unique_ptr<RegularPathExpr> invert() const override {
        return std::make_unique<PathKleeneStar>(path->invert());
    }
};
