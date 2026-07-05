//
// Created by heli on 8/22/24.
//

//
// Created by lhy on 8/9/24.
//

#pragma  once
#include <boost/algorithm/string/join.hpp>

#include "query/parser/paths/regular_path_expr.h"
#include "query/smt/lra/to_smt_lib.h"



class SMTAtom: public RegularPathExpr{
public:

    std::string atom;
    bool inverse;
    std::unique_ptr<SMT::Expr> property_checks;
    std::vector<std::pair<std::string, std::string>> reg_assignments;

    SMTAtom(std::string atom, bool inverse,
            std::unique_ptr<SMT::Expr>  property_checks) :

            atom    (atom),
            inverse (inverse),
            property_checks (std::move(property_checks)) {
    }

    SMTAtom(const SMTAtom& other) :

            atom    (other.atom),
            inverse (other.inverse),
            property_checks(std::unique_ptr<SMT::Expr>(other.property_checks->clone()) ),
            reg_assignments(other.reg_assignments)
    {

    }


    std::unique_ptr<RegularPathExpr> clone() const override {
        auto c = std::make_unique<SMTAtom>(atom, inverse, std::unique_ptr(property_checks->clone()));
        c->reg_assignments = reg_assignments;
        return c;
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
    SMTAutomaton get_smt_base_automaton() const override {
        // Create a simple automaton
        auto automaton = SMTAutomaton();
        automaton.end_states.insert(1);

        // Connect states with (atom, smtexpr) as label
        auto formula = SMT::ToSMTLibLRA::convert_expr(*property_checks);
        auto t = SMTTransition::make_transition(0, 1, inverse, atom,  formula );
        t.reg_assignments = reg_assignments;
        automaton.add_transition(std::move(t));
        return automaton;
    }

    std::unique_ptr<RegularPathExpr> invert() const override {
        auto inv = std::make_unique<SMTAtom>(atom, !inverse, std::unique_ptr(property_checks->clone()));
        inv->reg_assignments = reg_assignments;
        return inv;
    }
    std::set<VarId> get_var() const override
    {
        return property_checks->get_all_vars();
    }
    std::string to_string() const override {

        std::string property_string = SMT::ToSMTLibLRA::convert_expr(*property_checks);


        if (inverse) {
            return "^"  + atom  + "," + property_string;
        }
        return "" +atom + "," +  property_string;
    }
    std::set<std::tuple<std::string, ObjectId>> collect_attr() const override {
        auto attrs = property_checks->get_all_attrs();
        // Also add attributes from register assignments (e.g., ??edge0 = weight)
        for (const auto& [reg_name, attr_name] : reg_assignments) {
            auto oid = QuadObjectId::get_string(attr_name);
            attrs.emplace(attr_name, oid);
        }
        return attrs;
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










