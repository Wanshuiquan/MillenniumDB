import pickle
import sys
import time
import random
from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server


ICIJ_LEAK_SAMPLE = 10000
ICIJ_SIZE = 1908466
"""
A = Entity / same_as 
B = Officier / DIRECTOR_OF 
C = Intermediary / SHAREHOLDER_OF
"""

TEMPLATE_Q1 = "ANY ACYCLIC ?e :same_as*" 
TEMPLATE_Q2 = "ANY ACYCLIC ?e :same_as/:same_name_as*"
TEMPLATE_Q3 = "ANY ACYCLIC ?e :same_as?/:same_name_as*"
TEMPLATE_Q4 = "ANY ACYCLIC ?e :same_as/:same_name_as"
TEMPLATE_Q5 = "ANY ACYCLIC ?e :same_as*/:same_name_as*"
TEMPLATE_Q6 = "ANY ACYCLIC ?e :same_as/:same_name_as*/underlying*"
TEMPLATE_Q7 = "ANY ACYCLIC ?e :same_as/:same_name_as/underlying"
TEMPLATE_Q8 = "ANY ACYCLIC ?e :same_as/:same_name_as*/underlying"
TEMPLATE_Q9 = "ANY ACYCLIC ?e (:same_as | :same_name_as | underlying)*"
TEMPLATE_Q10 = "ANY ACYCLIC ?e (:same_as | :same_name_as | underlying)/:same_name_as*"

Q11 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q12 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*"
Q13 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7})/ ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7}))*"
Q14 = "DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id })/ ((:same_as {true} )/(Entity {?q - node_id <= 10 and node_id - ?q <= 10 and 0.5 * valid_until + 10 < ?p }))*"
Q15 = """DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 10 and node_id - ?q + ?p - valid_until <= 10 and node_id - ?q + valid_until - ?p <= 10 and ?q - node_id + valid_until - ?p <= 10})/ ((:same_as {true} )/ 
(Entity {?q - node_id + ?p - valid_until <= 10 and node_id - ?q + ?p - valid_until <= 10 and node_id - ?q + valid_until - ?p <= 10 and ?q - node_id + valid_until - ?p <= 10 }))*"""


Q21 = """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q22 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {?p >= valid_until and ?q <= valid_until} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((:same_name_as {?p >= valid_until and ?q <= valid_until} )/(Entity {?p >= valid_until and ?q <= valid_until}))*
"""



Q23 = """ 
       DATA_TEST ?e (people {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))/
                 ((:Favorite {true} )/(people {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*
"""


Q24 = """ 
       DATA_TEST ?e (people {?p == valid_until and ?q == node_id})/ 
                ((:Follow {true} )/(people {?q - node_id <= 10 and node_id - ?q <= 10 and 0.5 * valid_until + 10 < ?p}))/
                 ((:Favorite {true} )/(people {?q - node_id <= 10 and node_id - ?q <= 10 and 0.5 * valid_until + 10 < ?p}))*
"""

Q25 = """ 
       DATA_TEST ?e (people {?q - node_id + ?p - valid_until <= 10 and node_id - ?q + ?p - valid_until <= 10 and node_id - ?q + valid_until - ?p <= 10 and ?q - node_id + valid_until - ?p <= 10})/ 
                ((:Follow {true} )/(people {?q - node_id + ?p - valid_until <= 10 and node_id - ?q + ?p - valid_until <= 10 and node_id - ?q + valid_until - ?p <= 10 and ?q - node_id + valid_until - ?p <= 10 }))/
                 ((:Favorite {true} )/(people {?q - node_id + ?p - valid_until <= 10 and node_id - ?q + ?p - valid_until <= 10 and node_id - ?q + valid_until - ?p <= 10 and ?q - node_id + valid_until - ?p <= 10 }))*
"""

Q31 =  """
        DATA_TEST ?e (Entity {true})/ 
                ((:same_as {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {true}))?/
                 ((:same_name_as {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {true}))*
      
      """

Q32 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*
"""

Q41 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q42 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))
"""
Q51 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q52 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*
"""
Q61 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q62 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))*
"""

Q71 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q72 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*/
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))
"""

Q81 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q82 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((underlying {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))
"""

Q91 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15 })/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q92 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))*"

Q101 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/((underlying {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q102 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))/(underlying {true} )/((Entity {?p >= valid_until and ?q <= valid_until}))*"



# REGEX_TEMPLATE = [TEMPLATE_Q1, TEMPLATE_Q2, TEMPLATE_Q3, TEMPLATE_Q4, TEMPLATE_Q5, TEMPLATE_Q6, TEMPLATE_Q7, TEMPLATE_Q8, TEMPLATE_Q9, TEMPLATE_Q10]

# RDPR_TEMPLATE = [[Q11, Q12], [Q21, Q22], [Q31, Q32], [Q41, Q42], [Q151, Q152], [Q61, Q62], [Q71, Q72], [Q81, Q82], [Q91, Q92], [Q101, Q102]]
REGEX_TEMPLATE = [TEMPLATE_Q1, TEMPLATE_Q2, TEMPLATE_Q3, TEMPLATE_Q4, TEMPLATE_Q5, TEMPLATE_Q6, TEMPLATE_Q7, TEMPLATE_Q8, TEMPLATE_Q9, TEMPLATE_Q10]

RDPR_TEMPLATE = [[Q11, Q12, Q13, Q14, Q15], 
                 [Q21, Q22, Q23, Q24, Q25], 
                 [Q31, Q32, Q33, Q34, Q35], 
                 [Q41, Q42, Q43, Q44, Q45], 
                 [Q51, Q52, Q53, Q54, Q55], 
                 [Q61, Q62, Q63, Q64, Q65], 
                 [Q71, Q72, Q73, Q74, Q75], 
                 [Q81, Q82, Q83, Q84, Q85], 
                 [Q91, Q92, Q93, Q94, Q95], 
                 [Q101, Q102, Q103, Q104, Q105]]


def create_command(start_point: str, query: str):
    return f"Match ({start_point}) =[{query}] => (?to) \n Return * \n Limit 1"


def icij_graph_query():
 
    server = start_server(DBS_DIR / "icij-leak")
#     candidate = send_query("""MATCH (?from)=[DATA_TEST ?e (Entity {valid_until - ?p > 50 and ?p - valid_until < 50})/ ((:same_as {true} )/(Entity {valid_until - ?p > 50 and ?p - valid_until < 50}))*]=>(?to)
# RETURN ?from
# LIMIT 2000""").split("\n")[1:-1]
    candidate = []
    sample2 = send_query(f"Match (?x:Entity) Return ?x Limit 100000").split("\n")[1:-1]
    candidate_index = random.sample(range(100000), 10000)
    for i in candidate_index:
        candidate.append(sample2[i])
    result = []
    query_res = []
    # dating query

    id = 0
    for template_index in range(10):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        for index in candidate:
            sys.stdout.write(f"\rREGEX Q{template_index+1} " + str(id))
            sys.stdout.flush()
            id = id + 1

            query = create_command(str(index), regex_template)
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_dating.append((end_time - start_time) / 1000000)
            query_res_dating.append(query_result)
        result.append(("ICIJ_LEAK", f"REGEX Q{template_index+1}", res_dating))
        query_res.append(("ICIJ_LEAK", f"REGEX Q{template_index+1}", query_res_dating))

        rdpq_templates = RDPR_TEMPLATE[template_index]
    
        # money query 
        res_money = []
        query_res_money = []

        id = 0
        for index in candidate:
            sys.stdout.write(f"\rRDPQ Q{template_index+1}1 " + str(id))
            sys.stdout.flush()
            id = id + 1

            query = create_command(str(index), rdpq_templates[0])
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_money.append((end_time - start_time) / 1000000)
            query_res_money.append(query_result)
        result.append(("ICIJ_LEAK", f"RDPQ Q{template_index+1}1", res_money))
        query_res.append(("ICIJ_LEAK",f"RDPQ Q{template_index+1}1", query_res_money))

        #central path 
        res_centar = []
        query_res_centar = []

        id = 0
        for index in candidate:
            id = id + 1
            sys.stdout.write(f"\rRDPQ Q{template_index+1}2 " + str(id))
            sys.stdout.flush()
            query = create_command(str(index), rdpq_templates[1])
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_centar.append((end_time - start_time) / 1000000)
            query_res_centar.append(query_result)

        result.append(("ICIJ_LEAK", f"RDPQ Q{template_index+1}2", res_money))
        query_res.append(("ICIJ_LEAK",f"RDPQ Q{template_index+1}2", query_res_money))


   
        
    kill_server(server)
    with open(ROOT_TEST_DIR / "result" / "icij_static.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "icij_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)
        print("\n")
        print(len(candidate))

