import pickle
import sys
import time

from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server
from .query import create_query_command

LDBC_SAMPLE = 1000
"""
A = person / knows 
B = Officier / DIRECTOR_OF 
C = tagclass / SHAREHOLDER_OF
"""

TEMPLATE_Q1 = "ANY ACYCLIC ?e :knows*" 
TEMPLATE_Q2 = "ANY ACYCLIC ?e :knows/:hasInterest*"
TEMPLATE_Q3 = "ANY ACYCLIC ?e :knows?/:hasInterest*"
TEMPLATE_Q4 = "ANY ACYCLIC ?e :knows/:hasInterest"
TEMPLATE_Q5 = "ANY ACYCLIC ?e :knows*/:hasInterest*"
TEMPLATE_Q6 = "ANY ACYCLIC ?e :knows/:hasInterest*/hasType*"
TEMPLATE_Q7 = "ANY ACYCLIC ?e :knows/:hasInterest/hasType"
TEMPLATE_Q8 = "ANY ACYCLIC ?e :knows/:hasInterest*/hasType"
TEMPLATE_Q9 = "ANY ACYCLIC ?e (:knows | :hasInterest | hasType)*"
TEMPLATE_Q10 = "ANY ACYCLIC ?e (:knows | :hasInterest | hasType)/:hasInterest*"

Q11 = "DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ ((:knows {true} )/(person {oid - ?p > 15 and ?p - oid < 15}))*"
Q12 = "DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ ((:knows {true} )/(person {?p >= oid and ?q <= oid}))*"
Q13 = "DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?q - ?p <= 7})/ ((:knows {true} )/(person {?p >= oid and ?q <= oid and ?q - ?p <= 7}))*"
Q14 = "DATA_TEST ?e (person {?p == oid and ?q == iid })/ ((:knows {true} )/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 < ?p }))*"
Q15 = """DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ ((:knows {true} )/ 
(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 }))*"""


Q21 = """
        DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ 
                ((:knows {oid - ?p > 15 and ?p - oid < 15} )/(person {oid - ?p > 15 and ?p - oid < 15}))/
                 ((:hasInterest {oid - ?p > 15 and ?p - oid < 15} )/(tag {oid - ?p > 15 and ?p - oid < 15}))*
      
      """

Q22 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {?p >= oid and ?q <= oid} )/(person {?p >= oid and ?q <= oid}))/
                 ((:hasInterest {?p >= oid and ?q <= oid} )/(tag {?p >= oid and ?q <= oid}))*
"""

Q23 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p - ?q <= 7})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid and ?p - ?q  <= 7}))/
                 ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid and ?p - ?q <= 7}))*
"""


Q24 = """ 
       DATA_TEST ?e (person {?p == oid and ?q == iid})/ 
                ((:knows {true} )/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 < ?p}))/
                 ((:hasInterest {true} )/(tag {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 < ?p}))*
"""

Q25 = """ 
       DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ 
                ((:knows {true} )/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 }))/
                 ((:hasInterest {true} )/(tag {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 }))*
"""
Q31 =  """
        DATA_TEST ?e (person {true})/ 
                ((:knows {oid - ?p > 15 and ?p - oid < 15} )/(person {true}))?/
                 ((:hasInterest {oid - ?p > 15 and ?p - oid < 15} )/(tag {true}))*
      
      """

Q32 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid}))?/
                 ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid}))*
"""
Q33 = """ 
       DATA_TEST ?e (person {?p >= iid and ?q <= iid and ?p -?q <= 7})/ 
                ((:knows {true} )/(person {?p >= iid and ?q <= iid and ?p - ?q <= 7}))?/
                 ((:hasInterest {true} )/(tag {?p >= iid and ?q <= iid and ?p -?q <= 7}))*
"""


Q34 = """ 
       DATA_TEST ?e (person {?p == iid and ?q == oid})/ 
                ((:knows {true} )/(person {?q - oid <= 100 and oid - ?q <= 100 and 0.5 * iid + 100 < ?p}))?/
                 ((:hasInterest {true} )/(tag {?q - oid <= 100 and oid - ?q <= 100 and 0.5 * iid + 100 < ?p}))*
"""
Q35 = """ 
       DATA_TEST ?e (person {?q - oid + ?p - iid <= 100 and oid - ?q + ?p - iid <= 100 and oid - ?q + iid - ?p <= 100 and ?q - oid + iid - ?p <= 100})/ 
                ((:knows {true} )/(person {?q - oid + ?p - iid <= 100 and oid - ?q + ?p - iid <= 100 and oid - ?q + iid - ?p <= 100 and ?q - oid + iid - ?p <= 100}))?/
                 ((:hasInterest {true} )/(tag {?q - oid + ?p - iid <= 100 and oid - ?q + ?p - iid <= 100 and oid - ?q + iid - ?p <= 100 and ?q - oid + iid - ?p <= 100}))*
"""

Q41 =  """
        DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ 
                ((:knows {true} )/(person {oid - ?p > 15 and ?p - oid < 15}))/
                 ((:hasInterest {true} )/(tag {oid - ?p > 15 and ?p - oid < 15}))
      
      """

Q42 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid}))/
                 ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid}))
"""

Q43 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p -?q <= 7})/ 
                ((:knows {true} )/(person {?p >= oid and ?p - ?q <= 7}))/
                 ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid and ?p -?q <= 7}))
"""

Q44 = """ 
       DATA_TEST ?e (person {?p == oid and ?q == iid})/ 
                ((:knows {true} )/(person {?q - iid <= 100 and iid -?q <= 100 and  0.5 * oid + 100 <= ?p}))/
                 ((:hasInterest {true} )/(tag {?q - iid <= 100 and iid -?q <= 100 and  0.5 * oid + 100 <= ?p}))
"""

Q45 = """ 
       DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ 
                ((:knows {true} )/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))/
                 ((:hasInterest {true} )/(tag {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))
"""

Q51 =  """
        DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ 
                ((:knows {true} )/(person {oid - ?p > 15 and ?p - oid < 15}))*/
                 ((:hasInterest {true} )/(tag {oid - ?p > 15 and ?p - oid < 15}))*
      
      """

Q52 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid}))?/
                 ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid}))*
"""

Q53 =  """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p - ?q <= 7})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid and ?p - ?q <= 7}))?/
                 ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid and ?p - ?q  <= 7}))*
"""

Q54 = """ 
       DATA_TEST ?e (person {?p == oid and ?q == iid})/ 
                ((:knows {true} )/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))?/
                 ((:hasInterest {true} )/(tag {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))*
"""

Q55 = """ 
       DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 })/ 
                ((:knows {true} )/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 }))?/
                 ((:hasInterest {true} )/(tag {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 }))*
"""

Q61 =  """
        DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ 
                ((:knows {true} )/(person {oid - ?p > 15 and ?p - oid < 15}))/
                 ((:hasInterest {true} )/(tag {oid - ?p > 15 and ?p - oid < 15}))/ 
                 ((hasType {true} )/(tagclass {oid - ?p > 15 and ?p - oid < 15}))*
      
      """

Q62 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid}))/
                ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid}))/
                 ((hasType {true} )/(tagclass {?p >= oid and ?q <= oid}))*
"""
Q63 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p -?q <= 7})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid and ?p -?q <= 7}))/
                ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid and ?p -?q <= 7}))/
                 ((:hasType {true} )/(tagclass {?p >= oid and ?q <= oid and ?p - ?q <= 7}))*
"""

Q64 = """ 
       DATA_TEST ?e (person {?p == oid and ?q == iid})/ 
                ((:knows {true} )/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))/
                ((:hasInterest {true} )/(tag {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))/
                 ((:hasType {true} )/(tagclass {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))*
"""

Q65 = """ 
       DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ 
                ((:knows {true} )/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))/
                ((:hasInterest {true} )/(tag {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))/
                 ((:hasType {true} )/(tagclass {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))*
"""

Q71 =  """
        DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ 
                ((:knows {true} )/(person {oid - ?p > 15 and ?p - oid < 15}))/
                 ((:hasInterest {true} )/(tag {oid - ?p > 15 and ?p - oid < 15}))*/ 
                 ((hasType {true} )/(tagclass {oid - ?p > 15 and ?p - oid < 15}))
      
      """

Q72 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid}))/
                ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid}))*/
                 ((hasType {true} )/(tagclass {?p >= oid and ?q <= oid}))
"""
Q73 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p - ?q <= 7})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid and ?p - ?q <= 7}))/
                ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid and ?p - ?q <= 7 }))*/
                 ((:hasType {true} )/(tagclass {?p >= oid and ?q <= oid and ?p - ?q <= 7}))
"""

Q74 = """ 
       DATA_TEST ?e (person {?p == oid and ?q == iid})/ 
                ((:knows {true} )/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))/
                ((:hasInterest {true} )/(tag {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p }))*/
                 ((:hasType {true} )/(tagclass {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))
"""

Q75 = """ 
       DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ 
                ((:knows {true} )/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))/
                ((:hasInterest {true} )/(tag {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100 }))*/
                 ((:hasType {true} )/(tagclass {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))
"""

Q81 =  """
        DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ 
                ((:knows {true} )/(person {oid - ?p > 15 and ?p - oid < 15}))/
                 ((:hasInterest {true} )/(tag {oid - ?p > 15 and ?p - oid < 15}))/ 
                 ((hasType {true} )/(tagclass {oid - ?p > 15 and ?p - oid < 15}))
      
      """

Q82 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid}))/
                ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid}))/
                 ((hasType {true} )/(person {?p >= oid and ?q <= oid}))
"""

Q83 = """ 
       DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p - ?q <= 7})/ 
                ((:knows {true} )/(person {?p >= oid and ?q <= oid and ?p - ?q <= 7}))/
                ((:hasInterest {true} )/(tag {?p >= oid and ?q <= oid and ?p - ?q <= 7}))/
                 ((:hasType {true} )/(tagclass {?p >= oid and ?q <= oid and ?p - ?q  <= 7}))
"""

Q84 = """ 
       DATA_TEST ?e (person {?p == oid and ?q == iid})/ 
                ((:knows {true} )/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))/
                ((:hasInterest {true} )/(tag {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))/
                 ((:hasType {true} )/(tagclass {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))
"""

Q85 = """ 
       DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ 
                ((:knows {true} )/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))/
                ((:hasInterest {true} )/(tag {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))/
                 ((:hasType {true} )/(tagclass {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))"""

Q91 = "DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15 })/ (((:knows {true}) | (:hasInterest {true} ) | (hasType {true} ))/(person {oid - ?p > 15 and ?p - oid < 15}))*"
Q92 = "DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ (((:knows {true}) | (:hasInterest {true} ) | (hasType {true} ))/(person {?p >= oid and ?q <= oid}))*"
Q93 = "DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p - ?q <= 7})/ (((:knows {true}) | (:hasInterest {true} ) | (:hasType {true} ))/(person {?p >= oid and ?q <= oid and ?p - ?q <= 7}))*"
Q94 = "DATA_TEST ?e (person {?p == oid and ?q == iid})/ (((:knows {true}) | (:hasInterest {true} ) | (:hasType {true} ))/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))*"
Q95 = "DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ (((:knows {true}) | (:hasInterest {true} ) | (:hasType {true} ))/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100}))*"


Q101 = "DATA_TEST ?e (person {oid - ?p > 15 and ?p - oid < 15})/ (((:knows {true}) | (:hasInterest {true} ) | (hasType {true} ))/(person {oid - ?p > 15 and ?p - oid < 15}))/((hasType {true} )/(tagclass {oid - ?p > 15 and ?p - oid < 15}))*"
Q102 = "DATA_TEST ?e (person {?p >= oid and ?q <= oid})/ (((:knows {true}) | (:hasInterest {true} ) | (hasType {true} ))/(person {?p >= oid and ?q <= oid}))/(hasType {true} )/((tagclass {?p >= oid and ?q <= oid}))*"
Q103 = "DATA_TEST ?e (person {?p >= oid and ?q <= oid and ?p - ?q <= 7})/ (((:knows {true}) | (:hasInterest {true} ) | (:hasType {true} ))/(person {?p >= oid and ?q <= oid and ?p - ?q <= 7}))*"
Q104 = "DATA_TEST ?e (person {?p >= oid and ?q == iid})/ (((:knows {true}) | (:hasInterest {true} ) | (:hasType {true} ))/(person {?q - iid <= 100 and iid - ?q <= 100 and 0.5 * oid + 100 <= ?p}))*"
Q105 = "DATA_TEST ?e (person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})/ ((((:knows {true}) | (:hasInterest {true} ) | (:hasType {true} ))/(person {?q - iid + ?p - oid <= 100 and iid - ?q + ?p - oid <= 100 and iid - ?q + oid - ?p <= 100 and ?q - iid + oid - ?p <= 100})))*"


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
 
    server = start_server(DBS_DIR / "ldbc01")

    candidate = []

    result = []
    query_res = []
    # dating query

    id = 0
    for template_index in range(10):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        candidate= sample(1000, 182965)

        for index in candidate:
            sys.stdout.write(f"\rREGEX Q{template_index+1}" + str(id))
            sys.stdout.flush()
            id = id + 1
            
            query = create_query_command(str(index), regex_template)
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
                            query_command = create_query_command(str(index), query)
                            start_time = time.time_ns()
                            query_result = send_query(query_command)
                            end_time = time.time_ns()
                            res_money.append((end_time - start_time) / 1000000)
                            query_res_money.append(query_result)
                     result.append(("POKEC", f"RDPQ Q{template_index+1}{query_index}", res_money))
                     query_res.append(("POKEC",f"RDPQ Q{template_index+1}{query_index}", query_res_money))
                     query_index = query_index + 1

    


   
        
    kill_server(server)
    with open(ROOT_TEST_DIR / "result" / "ldbc01_static.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "ldbc01_paradise_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)