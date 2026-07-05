//
// Created by lhy on 8/27/24.
//
#include "query/parser/paths/automaton/smt_automaton.h"
#include "graph_models/object_id.h"

#include <cassert>
#include <map>
#include <set>
#include <stack>
#include <tuple>
#include <utility>

namespace {
struct SMTLabel {
    std::string type;
    std::string property_checks;
    bool inverse;
    std::vector<std::pair<std::string, std::string>> reg_assignments;

    bool operator<(const SMTLabel& other) const {
        return std::tie(type, property_checks, inverse, reg_assignments)
             < std::tie(other.type, other.property_checks, other.inverse, other.reg_assignments);
    }

    bool operator==(const SMTLabel& other) const {
        return type == other.type
            && property_checks == other.property_checks
            && inverse == other.inverse
            && reg_assignments == other.reg_assignments;
    }
};

struct PartitionSet {
    uint_fast32_t states;
    uint_fast32_t partitions_count;
    std::vector<uint_fast32_t> partition;

    PartitionSet(uint_fast32_t states_count, const std::vector<bool>& is_final_state) :
        states(states_count)
    {
        uint_fast32_t total_final_states = 0;
        for (const auto state_is_final : is_final_state) {
            if (state_is_final) {
                total_final_states++;
            }
        }

        if (total_final_states == states_count) {
            partitions_count = 1;
            partition.assign(states_count, 0);
            return;
        }

        partitions_count = 2;
        partition.reserve(states_count);
        for (uint_fast32_t s = 0; s < states_count; s++) {
            partition.push_back(is_final_state[s] ? 1 : 0);
        }
    }

    std::vector<uint_fast32_t> get_partition_states(uint_fast32_t partition_number) const {
        std::vector<uint_fast32_t> res;
        for (uint_fast32_t s = 0; s < states; s++) {
            if (partition[s] == partition_number) {
                res.push_back(s);
            }
        }
        return res;
    }
};

inline bool is_epsilon_transition(const SMTTransition& transition) {
    return transition.type == "epsilon" && transition.property_checks == "epsilon";
}
} // namespace


// Print the automaton
void SMTAutomaton::print(std::ostream& os) const {
    for (size_t i = 0; i < from_to_connections.size(); i++) {
        for (auto& t : from_to_connections[i]) {
            os << t.from << "=[" << (t.inverse ? "^" : "") << t.type << " {" << t.property_checks << "}]=>" << t.to << "\n";
        }
    }
    os << "distance to end: \n";
    for (size_t i = 0; i < distance_to_final.size(); i++) {
        os << i << ":" << distance_to_final[i] << "\n";
    }
    os << "end states: { ";
    for (auto& state : end_states) {
        os << state << "  ";
    }
    os << "}\n";
    os << "start state: " << start << "\n";
    os << "final state: " << final_state << "\n" << std::endl;
    os << "total_states" << total_states << std::endl;
}


// Combine two automatons
void SMTAutomaton::rename_and_merge(SMTAutomaton& other) {
    auto initial_states = total_states;
    for (size_t i = 0; i < other.from_to_connections.size(); i++) {
        for (auto& t : other.from_to_connections[i]) {
            auto transition = SMTTransition::make_transition(
                t.from + initial_states,
                t.to + initial_states,
                t.inverse,
                t.type,
                std::move(t.property_checks)
            );
            transition.reg_assignments = t.reg_assignments;

            add_transition(transition);
        }
    }

    std::set<uint32_t> new_end;
    for (auto& end_state : other.end_states) {
        new_end.insert(initial_states + end_state);
    }
    other.end_states = std::move(new_end);

    other.start = initial_states;
}


// Add new transition to automaton
void SMTAutomaton::add_transition(SMTTransition transition) {
    while (from_to_connections.size() <= transition.from ||
           from_to_connections.size() <= transition.to) {
        std::vector<SMTTransition> new_vec = std::vector<SMTTransition>();
        from_to_connections.push_back(std::move(new_vec));
    }
    while (to_from_connections.size() <= transition.from ||
           to_from_connections.size() <= transition.to) {
        std::vector<SMTTransition> new_vec = std::vector<SMTTransition>();
        to_from_connections.push_back(std::move(new_vec));
    }

    bool exists = false;
    for (auto& t : from_to_connections[transition.from]) {
        if (transition == t) {
            exists = true;
            break;
        }
    }

    if (!exists) {
        from_to_connections[transition.from].push_back(transition);
        to_from_connections[transition.to].push_back(transition);
    }
    total_states = from_to_connections.size();
}


// Transform automaton into a final automaton
void SMTAutomaton::transform_automaton(ObjectId(*f)(const std::string&)) {
    transform_by_nfa();
    for (size_t i = 0; i < from_to_connections.size(); i++) {
        for (auto& t : from_to_connections[i]) {
            if (!t.type.empty() && t.type[0] == ':') {
                t.type_id = f(t.type.erase(0, 1));
            } else {
                t.type_id = QuadObjectId::get_string(t.type);
            }
        }
    }
}


void SMTAutomaton::add_epsilon_transition(uint32_t from, uint32_t to) {
    add_transition(SMTTransition(from, to, false, "epsilon", "epsilon"));
}


void SMTAutomaton::transform_by_nfa() {
    auto rebuild_reverse_connections = [this]() {
        to_from_connections.clear();
        to_from_connections.resize(from_to_connections.size());
        for (size_t from = 0; from < from_to_connections.size(); from++) {
            for (const auto& transition : from_to_connections[from]) {
                to_from_connections[transition.to].push_back(transition);
            }
        }
        total_states = from_to_connections.size();
    };

    auto get_epsilon_closure = [this](uint32_t state) {
        std::set<uint32_t> epsilon_closure;
        std::set<uint32_t> visited;
        std::stack<uint32_t> open;
        open.push(state);

        while (!open.empty()) {
            auto current_state = open.top();
            open.pop();

            if (visited.find(current_state) != visited.end()) {
                continue;
            }
            visited.insert(current_state);

            for (const auto& transition : from_to_connections[current_state]) {
                if (is_epsilon_transition(transition)) {
                    epsilon_closure.insert(transition.to);
                    open.push(transition.to);
                }
            }
        }
        return epsilon_closure;
    };

    auto delete_epsilon_transitions = [this, &get_epsilon_closure, &rebuild_reverse_connections]() {
        for (size_t state = 0; state < from_to_connections.size(); state++) {
            auto epsilon_closure = get_epsilon_closure(state);

            for (const auto closure_state : epsilon_closure) {
                if (end_states.find(closure_state) != end_states.end()) {
                    end_states.insert(state);
                }
            }

            size_t transition_n = 0;
            while (transition_n < from_to_connections[state].size()) {
                if (is_epsilon_transition(from_to_connections[state][transition_n])) {
                    for (const auto closure_state : epsilon_closure) {
                        for (const auto& transition : from_to_connections[closure_state]) {
                            if (!is_epsilon_transition(transition)) {
                                auto new_t = SMTTransition::make_transition(
                                    state,
                                    transition.to,
                                    transition.inverse,
                                    transition.type,
                                    transition.property_checks
                                );
                                new_t.reg_assignments = transition.reg_assignments;
                                add_transition(std::move(new_t));
                            }
                        }
                    }
                    from_to_connections[state].erase(from_to_connections[state].begin() + transition_n);
                } else {
                    transition_n++;
                }
            }
        }
        rebuild_reverse_connections();
    };

    auto get_reachable_states = [this](uint32_t source, bool inverse) {
        std::stack<uint32_t> open;
        std::set<uint32_t> reachable_states;
        open.push(source);

        while (!open.empty()) {
            auto current_state = open.top();
            open.pop();

            if (reachable_states.find(current_state) != reachable_states.end()) {
                continue;
            }
            reachable_states.insert(current_state);

            const auto& transitions = inverse ? to_from_connections[current_state]
                                              : from_to_connections[current_state];
            for (const auto& transition : transitions) {
                open.push(inverse ? transition.from : transition.to);
            }
        }
        return reachable_states;
    };

    auto delete_unreachable_states = [this, &get_reachable_states, &rebuild_reverse_connections]() {
        auto reachable_states = get_reachable_states(start, false);

        for (size_t state = 0; state < from_to_connections.size(); state++) {
            if (reachable_states.find(state) == reachable_states.end()) {
                from_to_connections[state].clear();
                to_from_connections[state].clear();
                end_states.erase(state);
            }
        }

        for (size_t state = 0; state < from_to_connections.size(); state++) {
            auto& outgoing = from_to_connections[state];
            auto out_it = outgoing.begin();
            while (out_it != outgoing.end()) {
                if (reachable_states.find(out_it->to) == reachable_states.end()) {
                    out_it = outgoing.erase(out_it);
                } else {
                    ++out_it;
                }
            }

            auto& incoming = to_from_connections[state];
            auto in_it = incoming.begin();
            while (in_it != incoming.end()) {
                if (reachable_states.find(in_it->from) == reachable_states.end()) {
                    in_it = incoming.erase(in_it);
                } else {
                    ++in_it;
                }
            }
        }
        rebuild_reverse_connections();
    };

    delete_epsilon_transitions();
    delete_unreachable_states();

    std::stack<std::vector<bool>> open;
    std::set<std::vector<bool>> visited;
    std::map<std::vector<bool>, size_t> mapping;

    std::vector<std::vector<SMTTransition>> deterministic_from_to;
    std::vector<bool> deterministic_is_final;

    std::vector<bool> start_set(total_states, false);
    start_set[start] = true;
    open.push(start_set);
    mapping.insert({start_set, 0});

    deterministic_from_to.push_back({});
    deterministic_is_final.push_back(end_states.find(start) != end_states.end());

    size_t deterministic_state_count = 1;
    while (!open.empty()) {
        auto current_set = open.top();
        open.pop();

        auto current_state = mapping[current_set];

        if (visited.find(current_set) != visited.end()) {
            continue;
        }
        visited.insert(current_set);

        std::map<SMTLabel, std::vector<bool>> reached_grouped_by_label;
        std::map<SMTLabel, bool> reached_grouped_by_label_is_final;

        for (size_t state = 0; state < current_set.size(); state++) {
            if (!current_set[state]) {
                continue;
            }

            for (const auto& transition : from_to_connections[state]) {
                SMTLabel label{transition.type, transition.property_checks, transition.inverse, transition.reg_assignments};
                auto found_label = reached_grouped_by_label.find(label);
                if (found_label == reached_grouped_by_label.end()) {
                    std::vector<bool> new_set(total_states, false);
                    new_set[transition.to] = true;
                    reached_grouped_by_label.insert({label, new_set});
                    reached_grouped_by_label_is_final.insert(
                        {label, end_states.find(transition.to) != end_states.end()}
                    );
                } else {
                    found_label->second[transition.to] = true;
                    if (end_states.find(transition.to) != end_states.end()) {
                        reached_grouped_by_label_is_final[label] = true;
                    }
                }
            }
        }

        for (const auto& [label, reached_set] : reached_grouped_by_label) {
            auto mapping_found = mapping.find(reached_set);
            if (mapping_found == mapping.end()) {
                auto new_state = deterministic_state_count++;
                mapping.insert({reached_set, new_state});

                deterministic_from_to.push_back({});
                deterministic_is_final.push_back(reached_grouped_by_label_is_final[label]);
                deterministic_from_to[current_state].push_back(
                    SMTTransition::make_transition(
                        current_state,
                        new_state,
                        label.inverse,
                        label.type,
                        label.property_checks
                    )
                );
                deterministic_from_to[current_state].back().reg_assignments = label.reg_assignments;
                open.push(reached_set);
            } else {
                deterministic_from_to[current_state].push_back(
                    SMTTransition::make_transition(
                        current_state,
                        mapping_found->second,
                        label.inverse,
                        label.type,
                        label.property_checks
                    )
                );
                deterministic_from_to[current_state].back().reg_assignments = label.reg_assignments;
            }
        }
    }

    std::set<SMTLabel> alphabet_set;
    for (const auto& transitions : deterministic_from_to) {
        for (const auto& transition : transitions) {
            alphabet_set.emplace(SMTLabel{transition.type, transition.property_checks, transition.inverse, transition.reg_assignments});
        }
    }

    std::vector<SMTLabel> alphabet;
    std::map<SMTLabel, uint_fast32_t> alphabet_index;
    for (const auto& label : alphabet_set) {
        auto next_index = alphabet.size();
        alphabet.push_back(label);
        alphabet_index.insert({label, next_index});
    }

    std::vector<int64_t> transition_table(deterministic_from_to.size() * alphabet.size(), -1);
    auto result_transition = [&](uint_fast32_t state, uint_fast32_t alphabet_idx) -> int64_t& {
        return transition_table[state * alphabet.size() + alphabet_idx];
    };

    for (uint_fast32_t state = 0; state < deterministic_from_to.size(); state++) {
        for (const auto& transition : deterministic_from_to[state]) {
            SMTLabel label{transition.type, transition.property_checks, transition.inverse, transition.reg_assignments};
            auto label_idx = alphabet_index.at(label);
            result_transition(state, label_idx) = transition.to;
        }
    }

    PartitionSet current_set(deterministic_from_to.size(), deterministic_is_final);
    PartitionSet next_set(deterministic_from_to.size(), deterministic_is_final);

    do {
        current_set = next_set;

        int_fast32_t current_result_partition = -1;
        for (uint_fast32_t partition = 0; partition < current_set.partitions_count; partition++) {
            auto partition_states = current_set.get_partition_states(partition);
            assert(!partition_states.empty());

            next_set.partition[partition_states[0]] = ++current_result_partition;

            for (uint_fast32_t state_b_idx = 1; state_b_idx < partition_states.size(); state_b_idx++) {
                auto state_b = partition_states[state_b_idx];
                bool found_result_partition = false;

                for (uint_fast32_t state_a_idx = 0; state_a_idx < state_b_idx; state_a_idx++) {
                    auto state_a = partition_states[state_a_idx];
                    bool same_partition = true;

                    for (uint_fast32_t alp_idx = 0; alp_idx < alphabet.size(); alp_idx++) {
                        auto reached_a = result_transition(state_a, alp_idx);
                        auto reached_b = result_transition(state_b, alp_idx);

                        if (reached_a == -1 && reached_b == -1) {
                            continue;
                        }
                        if (reached_a == -1 || reached_b == -1) {
                            same_partition = false;
                            break;
                        }

                        if (current_set.partition[reached_a] != current_set.partition[reached_b]) {
                            same_partition = false;
                            break;
                        }
                    }

                    if (same_partition) {
                        next_set.partition[state_b] = next_set.partition[state_a];
                        found_result_partition = true;
                        break;
                    }
                }

                if (!found_result_partition) {
                    next_set.partition[state_b] = ++current_result_partition;
                }
            }
        }

        next_set.partitions_count = current_result_partition + 1;
    } while (current_set.partitions_count < next_set.partitions_count);

    std::vector<uint_fast32_t> partition_remap(current_set.partitions_count, 0);
    auto start_partition = current_set.partition[start];
    partition_remap[start_partition] = 0;

    uint_fast32_t next_partition_id = 1;
    for (uint_fast32_t partition = 0; partition < current_set.partitions_count; partition++) {
        if (partition == start_partition) {
            continue;
        }
        partition_remap[partition] = next_partition_id++;
    }

    std::vector<std::vector<SMTTransition>> minimized_from_to(current_set.partitions_count);
    std::vector<bool> minimized_is_final(current_set.partitions_count, false);

    for (uint_fast32_t state = 0; state < deterministic_from_to.size(); state++) {
        for (const auto& transition : deterministic_from_to[state]) {
            auto new_from = partition_remap[current_set.partition[transition.from]];
            auto new_to = partition_remap[current_set.partition[transition.to]];
            auto new_transition = SMTTransition::make_transition(
                new_from,
                new_to,
                transition.inverse,
                transition.type,
                transition.property_checks
            );
            new_transition.reg_assignments = transition.reg_assignments;

            bool already_exists = false;
            for (const auto& existing_transition : minimized_from_to[new_from]) {
                if (new_transition == existing_transition) {
                    already_exists = true;
                    break;
                }
            }

            if (!already_exists) {
                minimized_from_to[new_from].push_back(new_transition);
            }
        }

        if (deterministic_is_final[state]) {
            minimized_is_final[partition_remap[current_set.partition[state]]] = true;
        }
    }

    from_to_connections = std::move(minimized_from_to);
    rebuild_reverse_connections();

    start = 0;
    end_states.clear();
    for (size_t state = 0; state < minimized_is_final.size(); state++) {
        if (minimized_is_final[state]) {
            end_states.insert(state);
        }
    }

    final_state = end_states.size() == 1 ? *end_states.begin() : 0;
    distance_to_final.clear();
}
