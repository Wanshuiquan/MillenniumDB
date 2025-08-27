import pickle
import sys
import time

from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server
from .query import create_query_command

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
Q13 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7})/ ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7}))*"
Q14 = "DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id })/ ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p }))*"
Q15 = """DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ ((:OFFICER_OF {true} )/ 
(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*"""


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

Q23 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*
"""


Q24 = """ 
       DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p}))*
"""

Q25 = """ 
       DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*
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
Q33 = """ 
       DATA_TEST ?e (Officer {?p >= node_id and ?q <= node_id and ?p -?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q <= 7}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p -?q <= 7}))*
"""


Q34 = """ 
       DATA_TEST ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until <= 100 and valid_until - ?q <= 100 and 0.5 * node_id + 100 < ?p}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 100 and valid_until - ?q <= 100 and 0.5 * node_id + 100 < ?p}))*
"""
Q35 = """ 
       DATA_TEST ?e (Officer {?q - valid_until + ?p - node_id <= 100 and valid_until - ?q + ?p - node_id <= 100 and valid_until - ?q + node_id - ?p <= 100 and ?q - valid_until + node_id - ?p <= 100})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until + ?p - node_id <= 100 and valid_until - ?q + ?p - node_id <= 100 and valid_until - ?q + node_id - ?p <= 100 and ?q - valid_until + node_id - ?p <= 100}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 100 and valid_until - ?q + ?p - node_id <= 100 and valid_until - ?q + node_id - ?p <= 100 and ?q - valid_until + node_id - ?p <= 100}))*
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

Q43 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?p - ?q <= 7}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))
"""

Q44 = """ 
       DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id -?q <= 100 and  0.5 * valid_until + 100 <= ?p}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id <= 100 and node_id -?q <= 100 and  0.5 * valid_until + 100 <= ?p}))
"""

Q45 = """ 
       DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))
"""

Q51 =  """
        DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:OFFICER_OF {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q52 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until}))*
"""

Q53 =  """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))*
"""

Q54 = """ 
       DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*
"""

Q55 = """ 
       DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 })/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*
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
Q63 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*
"""

Q64 = """ 
       DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*
"""

Q65 = """ 
       DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))*
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
Q73 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7 }))*/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))
"""

Q74 = """ 
       DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p }))*/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))
"""

Q75 = """ 
       DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))
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

Q83 = """ 
       DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))
"""

Q84 = """ 
       DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))
"""

Q85 = """ 
       DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))"""

Q91 = "DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15 })/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q92 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))*"
Q93 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*"
Q94 = "DATA_TEST ?e (Officer {?p == valid_until and ?q == node_id})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*"
Q95 = "DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))*"


Q101 = "DATA_TEST ?e (Officer {valid_until - ?p > 15 and ?p - valid_until < 15})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/((INTERMEDIARY_OF {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q102 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (INTERMEDIARY_OF {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))/(INTERMEDIARY_OF {true} )/((Intermediary {?p >= valid_until and ?q <= valid_until}))*"
Q103 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*"
Q104 = "DATA_TEST ?e (Officer {?p >= valid_until and ?q == node_id})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*"
Q105 = "DATA_TEST ?e (Officer {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ ((((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})))*"


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
 
    server = start_server(DBS_DIR / "paradise")

    candidate = []

    result = []
    query_res = []
    # dating query

    id = 0
    for template_index in range(10):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        candidate= sample(100, 163414)

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
    with open(ROOT_TEST_DIR / "result" / "icij_paradise_static.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "icij_paradise_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)