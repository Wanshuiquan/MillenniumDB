//
// Created by lhy on 8/27/24.
//
#include "query/parser/paths/automaton/smt_automaton.h"
#include "graph_models/object_id.h"
#include <sstream>
#include <queue>
#include <stack>
#include <utility>
#include <boost/algorithm/string.hpp>
#include "query/smt/smt_expr/smt_expr_printer.h"



// Print the automaton
void SMTAutomaton::print(std::ostream& os) const {
    for (size_t i = 0; i < from_to_connections.size(); i++) {
        for (auto& t : from_to_connections[i]) {
            // TODO: print data check



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
    // Add and rename 'other' states to this automaton
    // Renaming consists in the sum of the original states
    // quantity to the id of 'other' states
    auto initial_states = total_states;
    for (size_t i = 0; i < other.from_to_connections.size(); i++) {
        for (auto& t : other.from_to_connections[i]) {
            // Create a transition with renamed states
            // Edge transition
                auto transition = SMTTransition::make_transition(
                        t.from + initial_states,
                        t.to + initial_states,
                        t.inverse,
                        t.type,
                        std::move(t.property_checks));

                // Add transition to this automaton
                add_transition(transition);

        }
    }

    // Rename 'other' end states
    std::set<uint32_t> new_end;
    for (auto& end_state : other.end_states) {
        new_end.insert(initial_states + end_state);
    }
    other.end_states = std::move(new_end);

    // Rename start state for 'other'
    other.start = initial_states;
}


// Add new transition to automaton
void SMTAutomaton::add_transition(SMTTransition transition) {
    // Check if connections vector has slots to save from and to
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

    // Check if the new connection already exists
    bool exists = false;
    for (auto& t : from_to_connections[transition.from]) {
        if (transition == t) {
            exists = true;
            break;
        }
    }

    // Add new connection only if it doesn't exist
    if (!exists) {
        from_to_connections[transition.from].push_back(transition);
        to_from_connections[transition.to].push_back(transition);
    }
    // Update number of states
    total_states = from_to_connections.size();
}


// Transform automaton into a final automaton
void SMTAutomaton::transform_automaton(ObjectId(*f)(const std::string&)) {
    transform_by_nfa();
    // Set transition ids
    for (size_t i = 0; i < from_to_connections.size(); i++) {
        for (auto& t : from_to_connections[i]) {
        if(t.type.c_str()[0] == ':') {
            t.type_id = f(t.type.erase(0, 1));
        }
        else{
            t.type_id = QuadObjectId::get_string(t.type);

        }
        }
    }
}
//
//// ----- Transformation handler methods -----
//
//
//// Collapses all end states into one final state
void SMTAutomaton::add_epsilon_transition(uint32_t from, uint32_t to){
    add_transition(SMTTransition(from, to, false, "epsilon", "epsilon"));
}


void SMTAutomaton::transform_by_nfa() {
    RPQ_NFA nfa;
    std::vector<std::string *> temp_pointer;
    // smt-aut -> dfa
    for (const auto& vec: from_to_connections){
        for (const auto& trans: vec){
            if (trans.type == "epsilon" && trans.property_checks == "epsilon"){
                nfa.add_epsilon_transition(trans.from, trans.to);
            }
            else{
                 std::string* t = new std::string(trans.type + "," + trans.property_checks);
                 temp_pointer.push_back(t);
                 nfa.add_transition(RPQ_NFA::Transition(trans.from, trans.to, t, trans.inverse));
            }
        }
    }

    nfa.end_states = std::move(end_states);
    nfa.delete_epsilon_transitions();
    nfa.delete_unreachable_states();
    RPQ_DFA dfa = nfa.transform_automaton(&QuadObjectId::get_string);

    // dfa -> smt-aut
    from_to_connections.clear();
    to_from_connections.clear();
    end_states.clear();

    for (const auto& vec: dfa.from_to_connections){
        for (const auto& transition:vec){
            auto t = decode_mask(transition.type_id);
            assert(std::holds_alternative<std::string>(t));
            std::vector<std::string> formula_and_type;
            boost::algorithm::split(formula_and_type,std::get<std::string>(t), boost::is_any_of(","));
            add_transition(SMTTransition(transition.from, transition.to, transition.inverse, formula_and_type[0], formula_and_type[1]));
        }
    }

    for (size_t i = 0; i < dfa.is_final_state.size(); i++){
        if (dfa.is_final_state[i]){
            end_states.insert(i);
        }
    }

    for (auto& p: temp_pointer) delete p;
}