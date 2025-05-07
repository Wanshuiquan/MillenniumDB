//
// Created by lhy on 8/27/24.
//

#ifndef MILLENNIUMDB_SMT_AUTOMATON_H
#define MILLENNIUMDB_SMT_AUTOMATON_H


#pragma once

#include <functional>
#include <ostream>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "query/var_id.h"
#include "query/smt/smt_expr/smt_exprs.h"
#include "rpq_automaton.h"
/*
This automaton also supports RDPQs (Data RPQs), where each node or edge
can evaluate it's properties (key: value) as a part of the path.

This automaton worked based on domain property graph model
// TODO: explain automaton structure (data transitions only have data checks, edge transitions have
// both data checks (for the edge) and type)
*/



// Transitions in the automaton (Edge & Data)
class SMTTransition {
public:
    // States connected by this transition
    uint_fast32_t from;
    uint_fast32_t to;

    // Direction of the transition (only applies to edge transitions)
    // false: from->to
    // true: to->from
    bool inverse;

    // Type of the transition for edge transitions
    // if is data transition type will be ""
    std::string type;

    ObjectId type_id;

    // List of property checks for the transition

    std::unique_ptr<SMT::Expr>  property_checks;
    // constructor
    SMTTransition(uint_fast32_t from, uint_fast32_t to, bool inverse, std::string type, std::unique_ptr<SMT::Expr> property):
    from (from),
    to (to),
    inverse (inverse),
    type (std::move(type)),
    property_checks(std::move(property))
    {

    }
    // constructor
    SMTTransition(uint_fast32_t from, uint_fast32_t to, bool inverse, std::string type, ObjectId type_id,std::unique_ptr<SMT::Expr> property):
            from (from),
            to (to),
            inverse (inverse),
            type (std::move(type)),
            type_id(type_id),
            property_checks(std::move(property))
    {

    }
    //copy constructor
    SMTTransition(const SMTTransition& other) :
            from (other.from),
            to (other.to),
            inverse (other.inverse),
            type (other.type),
            type_id(other.type_id)
    {
        if (other.property_checks == nullptr) {
            property_checks = nullptr;
        }
        else {
            property_checks = other.property_checks->clone();

        }

    }
    //clone function
    SMTTransition clone() const {
        return {from, to, inverse, type, type_id, property_checks->clone()};
    }

    // Transition equality
    bool operator==(const SMTTransition& other) const {
        // Data check transitions
        auto data = from == other.from && to == other.to && property_checks == other.property_checks;
        auto is_inverse = inverse == other.inverse;
        auto same_type = type ==other.type;
        return data && is_inverse && same_type;
    }

    SMTTransition& operator=(const SMTTransition& other){
         if (this ==  &other){
             return *this;
         }
         from = other.from;
         to = other.to;
         type =  other.type;
         inverse = other.inverse;
         type_id = other.type_id;
         property_checks = other.property_checks->clone();
        return  *this;


    }

    // Data transition constructor
    // We only consider edge transition
    static SMTTransition make_data_transition(uint_fast32_t from,
                                               uint_fast32_t to,
                                               std::unique_ptr<SMT::Expr>
                                               property_checks )
    {
        return {from, to, false, "", std::move(property_checks)};
    }

    // Edge transition constructor
    static std::unique_ptr<SMTTransition> make_edge_transition(uint_fast32_t from,
                                               uint_fast32_t to,
                                               bool inverse,
                                               const std::string& type,
                                               std::unique_ptr<SMT::Expr>
                                               property_checks)
    {
        return std::make_unique<SMTTransition>(from, to, inverse, type, std::move(property_checks));
    }

    // Edge transition constructor
    static SMTTransition make_transition(uint_fast32_t from,
                                         uint_fast32_t to,
                                         bool inverse,
                                         const std::string& type,
                                         std::unique_ptr<SMT::Expr>
                                              property_checks)
    {

               return {from, to, inverse, type, std::move(property_checks)};

    }
};


class SMTAutomaton {
private:
    // Start state, is always 0
    uint32_t start = 0;

    // Final state, will be set at the end of the automaton transformation
    uint32_t final_state = 0;

    // Number of states
    uint32_t total_states = 1;

    // the set of attributes 
    std::set<std::tuple<std::string, ObjectId>> attributes;
    std::set<std::tuple<std::string, ObjectId>> real_attributes;
    std::set<std::tuple<std::string, ObjectId>> string_attributes;

    // the set of parameters 
    std::set<VarId> parameter; 

    // ----- Methods to handle automaton transformations -----
    void transform_by_nfa();


public:
    // Transitions that start from the i-th state (stored in the i-th position)
    std::vector<std::vector<SMTTransition>> from_to_connections;

    // Transitions that reach the i-th state (stored in the i-th position)
    // These transitions will be invalid after transforming the automaton (prefer using from_to_connections)
    std::vector<std::vector<SMTTransition>> to_from_connections;

    // End states before the automaton transformation
    std::set<uint32_t> end_states;

    // Stores the distance to the end state. It can be used by the
    // A* algorithm in enum and check binding_iter algorithms.
    std::vector<uint32_t> distance_to_final;

    // Access attribute methods
    inline uint32_t get_start() const noexcept { return start; }
    inline uint32_t get_total_states() const noexcept  { return total_states; }
    inline bool decide_accept(uint64_t state) const noexcept {
        return (end_states.find(state)!= end_states.end());
    }
    inline std::set<std::tuple<std::string, ObjectId>> get_attr() const noexcept {return attributes;}
    // Print the automaton
    void print(std::ostream& os) const;

    // Add states from 'other' automaton to this automaton, rename 'other' states, update 'other'
    // end states to be consistent with rename. Don't update 'other' connections.
    void rename_and_merge(SMTAutomaton& other);

    // Add a transition to the automaton
    void add_transition(SMTTransition transition);

    // Apply transformations to get the final automaton
    void transform_automaton(ObjectId(*str_to_oid)(const std::string&));

    //add epsilon transition
    void add_epsilon_transition(uint32_t from, uint32_t to);
    // TODO: Refactor to modify the automaton instead of returning a new one
    // Returns the inverse automaton (invalidating this one)
    // RDPQAutomaton invert_automaton();

    //remove epsilon transitions

    // only for test
    void set_start(uint32_t x){
        start = x;
    }

    uint32_t get_start(){
        return start;
    }
    void set_final(std::set<uint32_t> x){
        end_states  = std::move(x);
    }

    u_int32_t get_total_state(){
        return total_states;
    }

    void set_attr(std::set<std::tuple<std::string, Sort, ObjectId>> attr){
        for (auto& a : attr) {
            auto name = std::get<0>(a);
            auto sort = std::get<1>(a);
            auto oid = std::get<2>(a);
            if (sort == Sort::String) {
                string_attributes.insert(std::make_tuple(name, oid));
                get_smt_ctx().add_string_var(name);
            }
            else {
                real_attributes.insert(std::make_tuple(name, oid));
                get_smt_ctx().add_real_var(name);
            }
            attributes.insert(std::make_tuple(name, oid));
        }
    }

        // the set of attributes 
    std::set<std::tuple<std::string, ObjectId>> get_attributes() {return attributes;};

    // the set of parameters 
    std::set<VarId> get_parameters(){return parameter;}; 

    void set_para(std::set<VarId> para){
        for (auto& p : para) {
            auto name = get_query_ctx().get_var_name(p);
            if (name != "epsilon") {
                get_smt_ctx().add_real_var(name);

            }
        }
        parameter = std::move(para); 
    }
};



#endif //MILLENNIUMDB_SMT_AUTOMATON_H
