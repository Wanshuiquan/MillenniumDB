//
// Created by heli on 8/22/24.
//

//
// Created by lhy on 8/9/24.
//

#pragma  once
#include <boost/algorithm/string/join.hpp>

#include "query/parser/paths/regular_path_expr.h"


// using object_atom = std::variant<std::monostate,std::string, ObjectId>;
// using formula = std::variant<std::monostate, std::unique_ptr<MQL::ExprAnd>, std::unique_ptr<SPARQL::ExprAnd>>;

class SMTAtom: public RegularPathExpr{
public:

    std::string atom;
    bool inverse;
    std::unique_ptr<SMT::Expr> property_checks;

    SMTAtom(std::string atom, bool inverse,
              std::unique_ptr<SMT::Expr>  property_checks) :

         atom    (atom),
         inverse (inverse),
         property_checks (std::move(property_checks)) {
    }

    SMTAtom(const SMTAtom& other) :

        atom    (other.atom),
        inverse (other.inverse),
        property_checks(std::unique_ptr<SMT::Expr>(other.property_checks->clone()) )
         {

    }


    std::unique_ptr<RegularPathExpr> clone() const override {

        return std::make_unique<SMTAtom>(atom, inverse, std::unique_ptr(property_checks->clone()));
    }

    PathType type() const override {
        return PathType::SMT_ATOM;
    }
    bool nullable() const override {
        return false;
    }

    RPQ_NFA get_rpq_base_automaton() const override {
        // Create a simple automaton
        auto automaton = RPQ_NFA();
        automaton.end_states.insert(1);
        // Connect states with atom as label
        // automaton.add_transition(RPQ_NFA::Transition(0, 1, &atom, inverse));
        return automaton;
    }

    RDPQAutomaton get_rdpq_base_automaton() const override {
        // Create a simple automaton
        auto automaton = RDPQAutomaton();

        //        // Empty data check first (D-state)
        //        automaton.add_transition(RDPQTransition::make_data_transition(0, 1));
        //
        //        // Add edge transition (E-state)
        //        auto data_checks = std::vector<property>();
        //        for (auto& property: property_checks) {
        //            data_checks.push_back(property);
        //        }
        //        std::sort(data_checks.begin(), data_checks.end());
        //        data_checks.erase(unique(data_checks.begin(), data_checks.end()), data_checks.end());
        //        automaton.add_transition(RDPQTransition::make_edge_transition(1, 2, inverse, atom, std::move(data_checks)));
        //
        //        // Add another empty data check (D-state)
        //        automaton.end_states.insert(3);
        //        automaton.add_transition(RDPQTransition::make_data_transition(2, 3));
        return automaton;
    }
    SMTAutomaton get_smt_base_automaton() const   {
        // Create a simple automaton
        auto automaton = SMTAutomaton();
        automaton.end_states.insert(1);
        // cast Expr to ExprAnd

        // Connect states with (atom, smtexpr) as label
        auto formula = property_checks ->to_smt_lib();
        automaton.add_transition(SMTTransition::make_transition(0, 1, inverse, atom,  formula ));
        return automaton;
    }

    std::unique_ptr<RegularPathExpr> invert() const override {

        return std::make_unique<SMTAtom>(atom, !inverse, std::unique_ptr(property_checks->clone()));
    }
    std::set<VarId> get_var() const
    {
        return property_checks->get_all_vars();
    }
     std::string to_string() const override {

             std::string property_string = property_checks ->to_smt_lib();


         if (inverse) {
             return "^"  + atom  + "," + property_string;
         }
         return "" +atom + "," +  property_string;
    }
    std::set<std::tuple<std::string, ObjectId>> collect_attr() const override {
        return property_checks ->get_all_attrs();
    }
    
    std::set<VarId> collect_para() const override {
        return property_checks ->get_all_parameter();
    }
     std::ostream& print_to_ostream(std::ostream& os, int indent = 0) const override {
       os << std::string(indent, ' ');
       os << "OpSMTAtom(" <<this -> to_string()<<")\n";
     return os;
    }
};











