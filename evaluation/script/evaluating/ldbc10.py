import pickle
import sys
import time
import random
from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server
from .query import create_query_command

LDBC_SAMPLE = 1000
"""
A = Person / KNOWS 
B = Officier / DIRECTOR_OF 
C = TagClass / SHAREHOLDER_OF
"""

TEMPLATE_Q1 = "ANY ACYCLIC ?e :KNOWS*" 
TEMPLATE_Q2 = "ANY ACYCLIC ?e :KNOWS/:HAS_INTEREST*"
TEMPLATE_Q3 = "ANY ACYCLIC ?e :KNOWS?/:HAS_INTEREST*"
TEMPLATE_Q4 = "ANY ACYCLIC ?e :KNOWS/:HAS_INTEREST"
TEMPLATE_Q5 = "ANY ACYCLIC ?e :KNOWS*/:HAS_INTEREST*"
TEMPLATE_Q6 = "ANY ACYCLIC ?e :KNOWS/:HAS_INTEREST*/HAS_TYPE*"
TEMPLATE_Q7 = "ANY ACYCLIC ?e :KNOWS/:HAS_INTEREST/HAS_TYPE"
TEMPLATE_Q8 = "ANY ACYCLIC ?e :KNOWS/:HAS_INTEREST*/HAS_TYPE"
TEMPLATE_Q9 = "ANY ACYCLIC ?e (:KNOWS | :HAS_INTEREST | HAS_TYPE)*"
TEMPLATE_Q10 = "ANY ACYCLIC ?e (:KNOWS | :HAS_INTEREST | HAS_TYPE)/:HAS_INTEREST*"

Q11 = "DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ ((:KNOWS {true} )/(Person {id - ?p > 15 and ?p - id < 15}))*"
Q12 = "DATA_TEST ?e (Person {?p >= id and ?q <= id})/ ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))*"
Q13 = "DATA_TEST ?e (Person {?p >= id and ?q <= id and ?q - ?p <= 7})/ ((:KNOWS {true} )/(Person {?p >= id and ?q <= id and ?q - ?p <= 7}))*"
Q14 = "DATA_TEST ?e (Person {?p == id and ?q == uid })/ ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 < ?p }))*"
Q15 = """DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ ((:KNOWS {true} )/ 
(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 }))*"""


Q21 = """
        DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ 
                ((:KNOWS {id - ?p > 15 and ?p - id < 15} )/(Person {id - ?p > 15 and ?p - id < 15}))/
                 ((:HAS_INTEREST {id - ?p > 15 and ?p - id < 15} )/(Tag {id - ?p > 15 and ?p - id < 15}))*
      
      """

Q22 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {?p >= id and ?q <= id} )/(Person {?p >= id and ?q <= id}))/
                 ((:HAS_INTEREST {?p >= id and ?q <= id} )/(Tag {?p >= id and ?q <= id}))*
"""

Q23 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p - ?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id and ?p - ?q  <= 7}))/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id and ?p - ?q <= 7}))*
"""


Q24 = """ 
       DATA_TEST ?e (Person {?p == id and ?q == uid})/ 
                ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 < ?p}))/
                 ((:HAS_INTEREST {true} )/(Tag {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 < ?p}))*
"""

Q25 = """ 
       DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ 
                ((:KNOWS {true} )/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 }))/
                 ((:HAS_INTEREST {true} )/(Tag {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 }))*
"""
Q31 =  """
        DATA_TEST ?e (Person {true})/ 
                ((:KNOWS {id - ?p > 15 and ?p - id < 15} )/(Person {true}))?/
                 ((:HAS_INTEREST {id - ?p > 15 and ?p - id < 15} )/(Tag {true}))*
      
      """

Q32 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id}))*
"""
Q33 = """ 
       DATA_TEST ?e (Person {?p >= uid and ?q <= uid and ?p -?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= uid and ?q <= uid and ?p - ?q <= 7}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= uid and ?q <= uid and ?p -?q <= 7}))*
"""


Q34 = """ 
       DATA_TEST ?e (Person {?p == uid and ?q == id})/ 
                ((:KNOWS {true} )/(Person {?q - id <= 100 and id - ?q <= 100 and 0.5 * uid + 100 < ?p}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?q - id <= 100 and id - ?q <= 100 and 0.5 * uid + 100 < ?p}))*
"""
Q35 = """ 
       DATA_TEST ?e (Person {?q - id + ?p - uid <= 100 and id - ?q + ?p - uid <= 100 and id - ?q + uid - ?p <= 100 and ?q - id + uid - ?p <= 100})/ 
                ((:KNOWS {true} )/(Person {?q - id + ?p - uid <= 100 and id - ?q + ?p - uid <= 100 and id - ?q + uid - ?p <= 100 and ?q - id + uid - ?p <= 100}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?q - id + ?p - uid <= 100 and id - ?q + ?p - uid <= 100 and id - ?q + uid - ?p <= 100 and ?q - id + uid - ?p <= 100}))*
"""

Q41 =  """
        DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ 
                ((:KNOWS {true} )/(Person {id - ?p > 15 and ?p - id < 15}))/
                 ((:HAS_INTEREST {true} )/(Tag {id - ?p > 15 and ?p - id < 15}))
      
      """

Q42 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id}))
"""

Q43 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p -?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?p - ?q <= 7}))/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id and ?p -?q <= 7}))
"""

Q44 = """ 
       DATA_TEST ?e (Person {?p == id and ?q == uid})/ 
                ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid -?q <= 100 and  0.5 * id + 100 <= ?p}))/
                 ((:HAS_INTEREST {true} )/(Tag {?q - uid <= 100 and uid -?q <= 100 and  0.5 * id + 100 <= ?p}))
"""

Q45 = """ 
       DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ 
                ((:KNOWS {true} )/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))/
                 ((:HAS_INTEREST {true} )/(Tag {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))
"""

Q51 =  """
        DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ 
                ((:KNOWS {true} )/(Person {id - ?p > 15 and ?p - id < 15}))*/
                 ((:HAS_INTEREST {true} )/(Tag {id - ?p > 15 and ?p - id < 15}))*
      
      """

Q52 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id}))*
"""

Q53 =  """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p - ?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id and ?p - ?q <= 7}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id and ?p - ?q  <= 7}))*
"""

Q54 = """ 
       DATA_TEST ?e (Person {?p == id and ?q == uid})/ 
                ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))?/
                 ((:HAS_INTEREST {true} )/(Tag {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))*
"""

Q55 = """ 
       DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 })/ 
                ((:KNOWS {true} )/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 }))?/
                 ((:HAS_INTEREST {true} )/(Tag {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 }))*
"""

Q61 =  """
        DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ 
                ((:KNOWS {true} )/(Person {id - ?p > 15 and ?p - id < 15}))/
                 ((:HAS_INTEREST {true} )/(Tag {id - ?p > 15 and ?p - id < 15}))/ 
                 ((HAS_TYPE {true} )/(TagClass {id - ?p > 15 and ?p - id < 15}))*
      
      """

Q62 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))/
                ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id}))/
                 ((HAS_TYPE {true} )/(TagClass {?p >= id and ?q <= id}))*
"""
Q63 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p -?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id and ?p -?q <= 7}))/
                ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id and ?p -?q <= 7}))/
                 ((:HAS_TYPE {true} )/(TagClass {?p >= id and ?q <= id and ?p - ?q <= 7}))*
"""

Q64 = """ 
       DATA_TEST ?e (Person {?p == id and ?q == uid})/ 
                ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))/
                ((:HAS_INTEREST {true} )/(Tag {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))/
                 ((:HAS_TYPE {true} )/(TagClass {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))*
"""

Q65 = """ 
       DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ 
                ((:KNOWS {true} )/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))/
                ((:HAS_INTEREST {true} )/(Tag {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))/
                 ((:HAS_TYPE {true} )/(TagClass {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))*
"""

Q71 =  """
        DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ 
                ((:KNOWS {true} )/(Person {id - ?p > 15 and ?p - id < 15}))/
                 ((:HAS_INTEREST {true} )/(Tag {id - ?p > 15 and ?p - id < 15}))*/ 
                 ((HAS_TYPE {true} )/(TagClass {id - ?p > 15 and ?p - id < 15}))
      
      """

Q72 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))/
                ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id}))*/
                 ((HAS_TYPE {true} )/(TagClass {?p >= id and ?q <= id}))
"""
Q73 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p - ?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id and ?p - ?q <= 7}))/
                ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id and ?p - ?q <= 7 }))*/
                 ((:HAS_TYPE {true} )/(TagClass {?p >= id and ?q <= id and ?p - ?q <= 7}))
"""

Q74 = """ 
       DATA_TEST ?e (Person {?p == id and ?q == uid})/ 
                ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))/
                ((:HAS_INTEREST {true} )/(Tag {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p }))*/
                 ((:HAS_TYPE {true} )/(TagClass {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))
"""

Q75 = """ 
       DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ 
                ((:KNOWS {true} )/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))/
                ((:HAS_INTEREST {true} )/(Tag {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100 }))*/
                 ((:HAS_TYPE {true} )/(TagClass {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))
"""

Q81 =  """
        DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ 
                ((:KNOWS {true} )/(Person {id - ?p > 15 and ?p - id < 15}))/
                 ((:HAS_INTEREST {true} )/(Tag {id - ?p > 15 and ?p - id < 15}))/ 
                 ((HAS_TYPE {true} )/(TagClass {id - ?p > 15 and ?p - id < 15}))
      
      """

Q82 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id}))/
                ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id}))/
                 ((HAS_TYPE {true} )/(Person {?p >= id and ?q <= id}))
"""

Q83 = """ 
       DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p - ?q <= 7})/ 
                ((:KNOWS {true} )/(Person {?p >= id and ?q <= id and ?p - ?q <= 7}))/
                ((:HAS_INTEREST {true} )/(Tag {?p >= id and ?q <= id and ?p - ?q <= 7}))/
                 ((:HAS_TYPE {true} )/(TagClass {?p >= id and ?q <= id and ?p - ?q  <= 7}))
"""

Q84 = """ 
       DATA_TEST ?e (Person {?p == id and ?q == uid})/ 
                ((:KNOWS {true} )/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))/
                ((:HAS_INTEREST {true} )/(Tag {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))/
                 ((:HAS_TYPE {true} )/(TagClass {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))
"""

Q85 = """ 
       DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ 
                ((:KNOWS {true} )/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))/
                ((:HAS_INTEREST {true} )/(Tag {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))/
                 ((:HAS_TYPE {true} )/(TagClass {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))"""

Q91 = "DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15 })/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (HAS_TYPE {true} ))/(Person {id - ?p > 15 and ?p - id < 15}))*"
Q92 = "DATA_TEST ?e (Person {?p >= id and ?q <= id})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (HAS_TYPE {true} ))/(Person {?p >= id and ?q <= id}))*"
Q93 = "DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p - ?q <= 7})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (:HAS_TYPE {true} ))/(Person {?p >= id and ?q <= id and ?p - ?q <= 7}))*"
Q94 = "DATA_TEST ?e (Person {?p == id and ?q == uid})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (:HAS_TYPE {true} ))/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))*"
Q95 = "DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (:HAS_TYPE {true} ))/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100}))*"


Q101 = "DATA_TEST ?e (Person {id - ?p > 15 and ?p - id < 15})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (HAS_TYPE {true} ))/(Person {id - ?p > 15 and ?p - id < 15}))/((HAS_TYPE {true} )/(TagClass {id - ?p > 15 and ?p - id < 15}))*"
Q102 = "DATA_TEST ?e (Person {?p >= id and ?q <= id})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (HAS_TYPE {true} ))/(Person {?p >= id and ?q <= id}))/(HAS_TYPE {true} )/((TagClass {?p >= id and ?q <= id}))*"
Q103 = "DATA_TEST ?e (Person {?p >= id and ?q <= id and ?p - ?q <= 7})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (:HAS_TYPE {true} ))/(Person {?p >= id and ?q <= id and ?p - ?q <= 7}))*"
Q104 = "DATA_TEST ?e (Person {?p >= id and ?q == uid})/ (((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (:HAS_TYPE {true} ))/(Person {?q - uid <= 100 and uid - ?q <= 100 and 0.5 * id + 100 <= ?p}))*"
Q105 = "DATA_TEST ?e (Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})/ ((((:KNOWS {true}) | (:HAS_INTEREST {true} ) | (:HAS_TYPE {true} ))/(Person {?q - uid + ?p - id <= 100 and uid - ?q + ?p - id <= 100 and uid - ?q + id - ?p <= 100 and ?q - uid + id - ?p <= 100})))*"


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
 
    server = start_server(DBS_DIR / "ldbc10")

    candidate = []

    result = []
    query_res = []
    # dating query

    id = 0
    for template_index in range(10):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        candidate_nodes = send_query(
             " Match (?s:Person) \n Return * \n"
        ).split("\n")[1:-1]

        candidate= random.sample(candidate_nodes, 10000)

        for index in candidate:
            sys.stdout.write(f"\rREGEX Q{template_index+1}" + str(id))
            sys.stdout.flush()
            id = id + 1
            
            query = create_command(str(index), regex_template)
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_dating.append((end_time - start_time) / 1000000)
            query_res_dating.append(query_result)
        result.append(("POKEC", f"REGEX Q{template_index}", res_dating))
        query_res.append(("POKEC", f"REGEX Q{template_index}", query_res_dating))

        rdpq_templates = RDPR_TEMPLATE[template_index]
    
        query_index = 1

        for query in rdpq_templates:
              # money query 
                     res_money = []
                     query_res_money = []
                     id = 0
                     for index in candidate:
                            sys.stdout.write(f"\rRDPQ Q{template_index+1}{query_index}  " + str(id))
                            sys.stdout.flush()
                            id = id + 1
                            query_command = create_command(str(index), query)
                            start_time = time.time_ns()
                            query_result = send_query(query_command)
                            end_time = time.time_ns()
                            res_money.append((end_time - start_time) / 1000000)
                            query_res_money.append(query_result)
                     result.append(("POKEC", f"RDPQ Q{template_index+1}{query_index}", res_money))
                     query_res.append(("POKEC",f"RDPQ Q{template_index+1}{query_index}", query_res_money))
                     query_index = query_index + 1

    


   
        
    kill_server(server)
    with open(ROOT_TEST_DIR / "result" / "ldbc10_static.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "ldbc10_paradise_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)