#include <z3++.h>
#include <map>
#include <vector>
#include <unordered_set>
#include <algorithm>
#include <iostream>

// standarlize linear arithmetic expressions
std::string normalize_linear_arithmetic(z3::context& ctx, z3::expr e) {
    std::map<std::string, int64_t> var_coeffs; // var -> coefficient
    int64_t constant = 0;                     // const
    z3::ast_vector todo(ctx);
    todo.push_back(e);
    while (!todo.empty()) {
        z3::expr current(ctx, todo.back());
        todo.pop_back();
        auto repl = current.to_string();
        // addtion
        if (current.decl().name().str() == "+") {
            for (unsigned i = 0; i < current.num_args(); i++) {
                todo.push_back(current.arg(i));
            }
        }
        // mulyiplication
        else if (current.decl().name().str() == "*" &&
                 current.num_args() == 2 &&
                 current.arg(0).is_numeral()) {
            int64_t coeff = current.arg(0).get_numeral_int64();
            z3::expr var = current.arg(1);
            if (var.is_const()) {
                var_coeffs[var.to_string()] += coeff;
            } else {
                // if not simple consts （like  *(2, (x + y))）, back to general solution
                todo.push_back(current);
            }
        }
        // const
        else if (current.is_numeral()) {
            constant += current.get_numeral_int64();
        }
        // var
        else if (current.is_const()) {
            var_coeffs[current.to_string()] =+ 1;
        }
        // non-linear vars
        else {
            return e.to_string();
        }
    }

    // reconstruct standard expressions
    std::string result = "0";

    for (const auto& [var, coeff] : var_coeffs) {
        if (coeff == 0) continue;
        // z3::expr var_expr = ctx.int_const(var.c_str());
        if (coeff == 1) {
            result = "(+ " + result + " " + var + ")";
        } else if (coeff == -1) {
            result = "(- " + result + " " + var + ")";
        } else {
            result = "(+ " + result + " (*" + std::to_string(coeff) + " " + var + "))";
        }
    }
    return result;
}

// 比较两个线性表达式是否等价
bool are_linear_exprs_equal(z3::context& ctx, z3::expr e1, z3::expr e2) {
    auto norm1 = normalize_linear_arithmetic(ctx, e1.simplify());
    auto norm2 = normalize_linear_arithmetic(ctx, e2.simplify());
    return norm1== norm2; // 标准化后字符串比较
}

void collect_constants_recursive(z3::expr const & e, std::unordered_set<std::string>& constants) {
    if (e.is_app()) {
        z3::func_decl f = e.decl();
        if (f.arity() == 0 && !e.is_numeral()) {  // Constants have arity 0 and aren't numerals
            constants.insert(f.name().str());
        }
        // Recursively visit children
        for (unsigned i = 0; i < e.num_args(); i++) {
            collect_constants_recursive(e.arg(i), constants);
        }
    }
    else if (e.is_quantifier()) {
        // Visit body of quantifier
        collect_constants_recursive(e.body(), constants);
    }
}

std::unordered_set<std::string> extract_constants(z3::expr const & formula) {
    std::unordered_set<std::string> constants;
    collect_constants_recursive(formula, constants);
    return constants;
}
// 测试用例
int main() {
    z3::context ctx;

    // Create a sample formula
    z3::expr a = ctx.constant("a", ctx.int_sort());
    z3::expr b = ctx.constant("b", ctx.int_sort());
    z3::expr c = ctx.constant("c", ctx.int_sort());
    z3::expr d = ctx.variable(1, ctx.int_sort());
    // z3::expr formula = (a + b == c) && (a > ctx.int_val(0));
    z3::expr formula = (d > a);
    // Extract constants
    auto constants = extract_constants(formula);
    z3::params params(ctx);
    // params.set("arith_lhs", true);
    params.set("arith_ineq_lhs", true);
    auto f = formula.simplify(params);
    // // Print the constants
    // std::cout << "Constants in the formula:\n";
    // for (const auto& decl : constants) {
    //     std::cout << decl << "\n";
    // }
   std::cout << f.to_string() << std::endl;

    return 0;
}