I want to also enable register variables in the mql regular expression by extend the mql syntax and the evaluation algoprithm, the register variable should be start by two `??', i.e.  ??x, ??y, ??z and so on. 

The idea of registers is based on the regular expressions with memories over datawords, by leonid libkin and domagoj

# Syntax
The syntax of constraint with registers should be extended as following 
??x = attribute1 , ??y = attribute2 in data-constraints, where ??x and ??y are register variables, and attribute1 and attribute2 are database attributes, and = is the assignment operator. 

if no register variable is updated, the syntax remains the same as before.

in the data constrains, the global parameters only have constant coefficients, but 
registers can have multiplication with database attributes 

if we have property p, register variable r and attributes a, we can have a⋅r but we can  not have 
a⋅p or r⋅p  

# SMTAutomaton 

if there are update of register variables in the data constraints, a transition need to store the updated register variables in the SMTAutomaton. The transition should have a new field to store the updated register variables and their corresponding values.


# Evaluation Algorithm 

In the evaluation algorithm, we should update the value of the register variables right after update the value of 
the database attributes. and then we should also instantiate the register variables in the evaluation algorithm immediately

# Testcases 
 you need to add new testcases by a new directory called `registers` in the `tests/mql` directory, and the testcases should cover the following scenarios:
 
- All values different than the first one
- Increasing values in edges/nodes
- Even edge values equal + odd edge values equal (different value in odd/even)