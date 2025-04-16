#include "search_state.h"
using namespace Paths::DataTest;


void PathState::print(std::ostream& os,
                      std::function<void(std::ostream& os, ObjectId)> print_node,
                      std::function<void(std::ostream& os, ObjectId, bool)> print_edge,
                      bool begin_at_left) const
{
    if (begin_at_left) {
        // the path need to be reconstructed in the reverse direction (last seen goes first)
        std::vector<ObjectId> nodes;
        std::vector<ObjectId> edges;
        std::vector<bool>     inverse_directions;

        for (auto current_state = this; current_state != nullptr; current_state = current_state->prev_state) {
            nodes.push_back(current_state->node_id);
            edges.push_back(current_state->type_id);
            inverse_directions.push_back(current_state->inverse_dir);
        }

        print_node(os, nodes[nodes.size() - 1]);
        for (int_fast32_t i = nodes.size() - 2; i >= 0; i--) { // don't use unsigned i, will overflow
            print_edge(os, edges[i], inverse_directions[i]);
            print_node(os, nodes[i]);
        }
    } else {
        auto current_state = this;
        print_node(os, current_state->node_id);

        while (current_state->prev_state != nullptr) {
            print_edge(os, current_state->type_id, !current_state->inverse_dir);
            current_state = current_state->prev_state;
            print_node(os, current_state->node_id);
        }
    }
}




int MacroState::update_bound(std::tuple<Bound, z3::expr, z3::expr> bound) {
    auto type = std::get<0>(bound);
    auto key = std::get<1>(bound);
    std::string key_str = get_smt_ctx().normalize_linear_arithmetic(key);
    auto value =  std::get<2>(bound);

    collected_expr.push_back(key);
    update_dependency_graph(key);
    switch (type) {
        case Le:{
            if (upper_bounds.find(key_str) == upper_bounds.end()){
                upper_bounds[key_str] = value.as_double();
            }
            else{
                double old_bound = upper_bounds[key_str];
                double new_bound = value.as_double();
                if (new_bound < old_bound) upper_bounds[key_str] = new_bound;
            }
            return 1;
        }
        case Ge:{
            if (lower_bounds.find(key_str) == lower_bounds.end()){
                lower_bounds[key_str] = value.as_double();
            }
            else{
                double old_bound = lower_bounds[key_str];
                double new_bound = value.as_double();
                if (new_bound > old_bound) lower_bounds[key_str] = new_bound;
            }
            return 1;
        }
        case EQ:{
            if (eq_vals.find(key_str) == eq_vals.end()){
                eq_vals[key_str] = value.as_double();
                return 1;
            }
            else{
                double old_bound = eq_vals[key_str];
                double new_bound = value.as_double();
                return int(new_bound == old_bound);
            }
        }
        default: return 0;
    }

}

std::set<std::string> MacroState::get_dependencies(std::string term)
{
    std::set<std::string> dependencies;
    auto rely_vars = terms2vars[term];
    for (const auto&var: rely_vars) {
        auto it = vars2terms.find(var);
        auto val = it -> second;
        dependencies.insert(vars2terms[var].begin(), vars2terms[var].end());
    }
    return dependencies;
}

void MacroState::build_dependency_graph()
{
    for (const auto& term: collected_expr) {
        update_dependency_graph(term);
    }
}

void MacroState::update_dependency_graph(z3::expr formula)
{
    // update the term2vars
    std::unordered_set<std::string> vars = get_smt_ctx().extract_constants(formula);
    std::string key = get_smt_ctx().normalize_linear_arithmetic(formula);


    //calculate the var2terns
    for (const auto& var: vars){
        if (vars2terms.find(var) == vars2terms.end())
        {
            vars2terms[var] = {key};
        }
        else {
            vars2terms[var].emplace(key);
        }
    }

    terms2vars[key] = std::move(vars);
}

bool MacroState::is_independent(std::string term)
{
    std::set<std::string> terms = get_dependencies(term);
    if (terms.size() == 1 && terms.find(term) != terms.end()) return true;
    return false;
}

bool MacroState::compute_bounds_without_z3(std::string key)
{
    {   double val = 0; bool have_eq = false;
        double up = 0; bool have_up = false;
        double low  = 0; bool have_low = false;
        bool res = true;
        if (eq_vals.find(key) != eq_vals.end()){
            val = eq_vals[key]; have_eq = true;
        }
        if (upper_bounds.find(key) != upper_bounds.end()) {
            up = upper_bounds[key]; have_up = true;
        }
        if (lower_bounds.find(key) != lower_bounds.end()) {
            low = lower_bounds[key]; have_low = true;
        }

        if (have_eq && have_low) {res = val >= low;}
        if (have_eq && have_up) {res = res & val <= up;}
        if (have_low && have_up) {res = res & val <= up & val >= low;}
        return res;
    }
}

void MacroState::set_model(z3::solver& s, std::map<VarId, double>& vars)
{
    std::set<std::string> visited_parameter;
    for (const auto& para: collected_expr){
        const std::string& key_str = get_smt_ctx().normalize_linear_arithmetic(para);
        if (visited_parameter.find(key_str) != visited_parameter.end()) {
            continue;
        }else {
            visited_parameter.emplace(key_str);
        }

   
           
        auto parameter = para;
        if (upper_bounds.find(key_str) != upper_bounds.end()){
                double val = upper_bounds[key_str];
                s.add(parameter <= get_smt_ctx().add_real_val(val));
            }
        if ( lower_bounds.find(key_str) !=  lower_bounds.end()){
                double val =  lower_bounds[key_str];
                s.add(parameter >= get_smt_ctx().add_real_val(val));
            }
        if ( eq_vals.find(key_str) !=  eq_vals.end()){
                double val =  eq_vals[key_str];
                s.add(parameter == get_smt_ctx().add_real_val(val));
            }
        }

    s.push();
    //check the sat for the current bound
    s.add(get_smt_ctx().bound_epsilon);
    SMTCtx::log_calling(s.to_smt2());

    switch (s.check()) {
    case z3::sat: {
        auto model = s.get_model();
        for (const auto &ele:vars){
            std::string name = get_query_ctx().get_var_name(ele.first);
            z3::expr v = get_smt_ctx().get_var(name);
            auto val = model.eval(v).as_double();
            vars[ele.first] = val;
        }
        s.pop();
        return;
    }
    case z3::unsat: s.pop(); return;
    case z3::unknown: s.pop(); return;
    }
}

