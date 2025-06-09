import pickle
import sys
import time

from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server


PARADISE_SAMPLE = 1000
"""
A = Officer / OFFICER_OF 
B = Officier / DIRECTOR_OF 
C = Intermediary / SHAREHOLDER_OF
"""

TEMPLATE_Q1 = "ANY ACYCLIC ?e :OFFICER_OF*" 
TEMPLATE_Q2 = "ANY ACYCLIC ?e :OFFICER_OF/:REGISTERED_ADDRESS*"
TEMPLATE_Q3 = "ANY ACYCLIC ?e :OFFICER_OF?/:REGISTERED_ADDRESS*"
TEMPLATE_Q4 = "ANY ACYCLIC ?e :OFFICER_OF/:REGISTERED_ADDRESS"
TEMPLATE_Q5 = "ANY ACYCLIC ?e :OFFICER_OF*/:REGISTERED_ADDRESS*"
TEMPLATE_Q6 = "ANY ACYCLIC ?e :OFFICER_OF/:REGISTERED_ADDRESS*/INTERMEDIARY_OF*"
TEMPLATE_Q7 = "ANY ACYCLIC ?e :OFFICER_OF/:REGISTERED_ADDRESS/INTERMEDIARY_OF"
TEMPLATE_Q8 = "ANY ACYCLIC ?e :OFFICER_OF/:REGISTERED_ADDRESS*/INTERMEDIARY_OF"
TEMPLATE_Q9 = "ANY ACYCLIC ?e (:OFFICER_OF | :REGISTERED_ADDRESS | INTERMEDIARY_OF)*"
TEMPLATE_Q10 = "ANY ACYCLIC ?e (:OFFICER_OF | :REGISTERED_ADDRESS | INTERMEDIARY_OF)/:REGISTERED_ADDRESS*"

Q11 = "DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q12 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*"


Q21 = """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:REGISTERED_ADDRESS {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q22 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {?p >= valid_until and ?q <= valid_until} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((:REGISTERED_ADDRESS {?p >= valid_until and ?q <= valid_until} )/(Address {?p >= valid_until and ?q <= valid_until}))*
"""

Q31 =  """
        DATA_TEST ?e (Officer {true})/ 
                ((:OFFICER_OF {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {true}))?/
                 ((:REGISTERED_ADDRESS {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Address {true}))*
      
      """

Q32 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))*
"""

Q41 =  """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q42 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))
"""
Q151 =  """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q152 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))*
"""
Q61 =  """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))/ 
                 ((INTERMEDIARY_OF {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q62 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))/
                 ((INTERMEDIARY_OF {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))*
"""

Q71 =  """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))*/ 
                 ((INTERMEDIARY_OF {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q72 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))*/
                 ((INTERMEDIARY_OF {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))
"""

Q81 =  """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))/ 
                 ((INTERMEDIARY_OF {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q82 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))/
                 ((INTERMEDIARY_OF {true} )/(Officer {?p >= valid_until and ?q <= valid_until}))
"""

Q91 = "DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15 })/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q92 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))*"

Q101 = "DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/((INTERMEDIARY_OF {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q102 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))/(INTERMEDIARY_OF {true} )/((Intermediary {?p >= valid_until and ?q <= valid_until}))*"



REGEX_TEMPLATE = [TEMPLATE_Q1, TEMPLATE_Q2, TEMPLATE_Q3, TEMPLATE_Q4, TEMPLATE_Q5, TEMPLATE_Q6, TEMPLATE_Q7, TEMPLATE_Q8, TEMPLATE_Q9, TEMPLATE_Q10]

RDPR_TEMPLATE = [[Q11, Q12], [Q21, Q22], [Q31, Q32], [Q41, Q42], [Q151, Q152], [Q61, Q62], [Q71, Q72], [Q81, Q82], [Q91, Q92], [Q101, Q102]]
def create_command(start_point: str, query: str):
    return f"Match ({start_point}) =[{query}] => (?to) \n Return * \n Limit 1"


def paradise_graph_query():

    server = start_server(DBS_DIR / "paradise")
    candidate = send_query(f"Match (?x:Officer) Return * Limit {PARADISE_SAMPLE}").split("\n")[1:-1]
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
        result.append(("PARADISE", f"REGEX Q{template_index+1}", res_dating))
        query_res.append(("PARADISE", f"REGEX Q{template_index+1}", query_res_dating))

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
        result.append(("PARADISE", f"RDPQ Q{template_index+1}1", res_money))
        query_res.append(("PARADISE",f"RDPQ Q{template_index+1}1", query_res_money))

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

        result.append(("PARADISE", f"RDPQ Q{template_index+1}2", res_money))
        query_res.append(("PARADISE",f"RDPQ Q{template_index+1}2", query_res_money))


   
        
    kill_server(server)
    with open(ROOT_TEST_DIR / "result" / "PARADISE_static.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "PARADISE_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)
        print("\n")
        print(len(candidate))

