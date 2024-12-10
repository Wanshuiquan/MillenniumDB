MONEY_QUERY = "DATA_TEST ?e (person {?p - ?q < 7 and ?p > age and ?q < age})/ ((:A {true}) /(person { ?p - ?q < 7 and ?p > age and ?q < age }))+"

DATING_QUERY_FB = """DATA_TEST ?e (person {?p == age and ?x == pos_x and ?y == pos_y})/ ((:A {true})/(person {true}))*/(:A {true}) /(person {
?p * 0.5 + 7 <= age
and  (?x - pos_x) + (?y - pos_y) <= 20 and
        (?x - pos_x) + (pos_y - ?y) <= 20 and
        (pos_x - ?x) + (?y - pos_y) <= 20 and
        (pos_x - ?x) + (pos_y - ?y) <= 20 and status == "single"
})
"""

DATING_QUERY_YTB = """DATA_TEST ?e (person {?p == age and ?x == pos_x and ?y == pos_y})/ ((:B {true})/(person {true}))*/(:B {true}) /(person {
?p * 0.5 + 7 <= age
and  (?x - pos_x) + (?y - pos_y) <= 20 and
        (?x - pos_x) + (pos_y - ?y) <= 20 and
        (pos_x - ?x) + (?y - pos_y) <= 20 and
        (pos_x - ?x) + (pos_y - ?y) <= 20 and status == "single"
})
"""

CENTRAL_PATH_QUERY = """ DATA_TEST ?e
(person {
 (?x - pos_x) + (?y - pos_y) <= 35 and
    (?x - pos_x) + (pos_y - ?y) <= 35 and
    (pos_x - ?x) + (?y - pos_y) <= 35 and
    (pos_x - ?x) + (pos_y - ?y) <= 35
})/ ((:A {true}) /(person {
    (?x - pos_x) + (?y - pos_y) <= 35 and
    (?x - pos_x) + (pos_y - ?y) <= 35 and
    (pos_x - ?x) + (?y - pos_y) <= 35 and
    (pos_x - ?x) + (pos_y - ?y) <= 35
}))*
"""

CENTRAL_PATH_QUERY_BIG = """ DATA_TEST ?e
(person {
 (?x - pos_x) + (?y - pos_y) <= 350 and
    (?x - pos_x) + (pos_y - ?y) <= 350 and
    (pos_x - ?x) + (?y - pos_y) <= 350 and
    (pos_x - ?x) + (pos_y - ?y) <= 350
})/ ((:A {true}) /(person {
    (?x - pos_x) + (?y - pos_y) <= 350 and
    (?x - pos_x) + (pos_y - ?y) <= 350 and
    (pos_x - ?x) + (?y - pos_y) <= 350 and
    (pos_x - ?x) + (pos_y - ?y) <= 350
}))*
"""

DATING_QUERY_POKEC = """
DATA_TEST ?e (people {?p == AGE and ?x == completion_percentage and ?g == gender})/ ((:follow {true})/(people {true}))*/(:follow {true}) /(people {
               ?p * 0.5 + 7 <= AGE
               and  ?x - completion_percentage <= 50  and
               completion_percentage - ?x <= 50 and 
              ?g == gender
               })
"""
CENTRAL_PATH_POKEC = """ DATA_TEST ?e
(people {
 (?x - completion_percentage) + (?y - AGE) <= 35 and
    (?x - completion_percentage) + (AGE - ?y) <= 35 and
    (completion_percentage - ?x) + (?y - AGE) <= 35 and
    (completion_percentage - ?x) + (AGE - ?y) <= 35
})/ ((:follow {true}) /(people {
    (?x - completion_percentage) + (?y - AGE) <= 35 and
    (?x - completion_percentage) + (AGE - ?y) <= 35 and
    (completion_percentage - ?x) + (?y - AGE) <= 35 and
    (completion_percentage - ?x) + (AGE - ?y) <= 35
}))*
"""
MONEY_QUERY_POKEC = "DATA_TEST ?e (people {?p - ?q < 30 and ?p > AGE and ?q < AGE})/ ((:follow {true}) /(people { ?p - ?q < 30 and ?p > AGE and ?q < AGE }))+"

def create_query_command(start_point: str, query: str):
    return f"Match (N{start_point}) =[{query}] => (?to) \n Return * \n Limit 10"
