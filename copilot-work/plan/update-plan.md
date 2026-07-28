

## Goal

1. The register variable should be parse into smt_expr/expr/expr_register.h 
2. implement the subset order of nra/nia according to lia and lra 
3. implement the models order by only leverage the entailment pipleline of nia for lia lra nia and nra 
4. implement model order with  ai of nra by leverage the pipeline of nia, you can abstract into 64 bits abstract interpretation 
5. if a global parameter is multiplied by register or another global parameter, then it should be use nia/nra 

for lia/lra, heavy optimization should connect to model_order 
for nia/nra, light optimization should connect to subset order and mid optimization should connect to model_order heavy optimization should connect to model_order_with_ai 


you should iterate until pass all testcases by running ./scripts/run-tests mql

