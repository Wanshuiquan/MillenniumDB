import json
import sys
import time

from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server, write_pickle
from .query import create_query_command

PARADISE_SAMPLE = 1000
"""
A = Officer / OFFICER_OF 
B = Officier / DIRECTOR_OF 
C = Intermediary / SHAREHOLDER_OF
"""


TEMPLATE_Q0 = "ANY SIMPLE ?e (:OFFICER_OF | :REGISTERED_ADDRESS | :INTERMEDIARY_OF)* "
TEMPLATE_Q1 =  "ANY SIMPLE ?e :OFFICER_OF*" 
TEMPLATE_Q2 = "ANY SIMPLE ?e :OFFICER_OF/:REGISTERED_ADDRESS/:INTERMEDIARY_OF"
TEMPLATE_Q3 = "ANY SIMPLE ?e :OFFICER_OF*/:REGISTERED_ADDRESS"
TEMPLATE_Q4 = "ANY SIMPLE ?e (:OFFICER_OF | :REGISTERED_ADDRESS | :INTERMEDIARY_OF) "
TEMPLATE_Q5 =  "ANY SIMPLE ?e :OFFICER_OF+" 
TEMPLATE_Q6 = "ANY SIMPLE ?e :OFFICER_OF?/:REGISTERED_ADDRESS?/:INTERMEDIARY_OF?"
TEMPLATE_Q7 = "ANY SIMPLE ?e :OFFICER_OF/(:REGISTERED_ADDRESS | :INTERMEDIARY_OF)"
TEMPLATE_Q8 = "ANY SIMPLE ?e :OFFICER_OF/:REGISTERED_ADDRESS?/:INTERMEDIARY_OF?"
TEMPLATE_Q9 = "ANY SIMPLE ?e (:OFFICER_OF/:REGISTERED_ADDRESS*)|:INTERMEDIARY_OF"
TEMPLATE_Q10 = "ANY SIMPLE ?e :OFFICER_OF?/:REGISTERED_ADDRESS*"
TEMPLATE_Q11 = "ANY SIMPLE ?e :OFFICER_OF/:REGISTERED_ADDRESS/:INTERMEDIARY_OF*"

Q01 = "DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/((:INTERMEDIARY_OF {true} )/(Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*"
Q02 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?p >= node_id and ?q <= node_id}))/(:INTERMEDIARY_OF {true} )/((Officer {?p >= node_id and ?q <= node_id}))*"
Q03 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))*"
Q04 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q == valid_until})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))*"
Q05 = "DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ ((((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})))*"


Q11 = "DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*"
Q12 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))*"
Q13 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?q - ?p <= 0.7})/ ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?q - ?p <= 0.7}))*"
Q14 = "DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until })/ ((:OFFICER_OF {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 < ?p }))*"
Q15 = """DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ ((:OFFICER_OF {true} )/ 
(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))*"""

Q21 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/ 
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {node_id - ?p > 0.3 and ?p - node_id < 0.3}))
      
      """

Q22 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id}))
"""


Q23 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id and ?p - ?q  <= 0.7}))
"""

Q24 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))
"""

Q25 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))"""


Q31 = """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {node_id - ?p > 0.3 and ?p - node_id < 0.3} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*/
                 ((:REGISTERED_ADDRESS {node_id - ?p > 0.3 and ?p - node_id < 0.3} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))
      
      """

Q32 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {?p >= node_id and ?q <= node_id} )/(Entity {?p >= node_id and ?q <= node_id}))*/
                 ((:REGISTERED_ADDRESS {?p >= node_id and ?q <= node_id} )/(Address {?p >= node_id and ?q <= node_id}))
"""



Q33 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q  <= 0.7}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))
"""


Q34 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 < ?p}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 < ?p}))
"""

Q35 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))
"""



Q41 = "DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3 })/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*"
Q42 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?p >= node_id and ?q <= node_id}))*"
Q43 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))*"
Q44 = "DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))*"
Q45 = "DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ (((:OFFICER_OF {true}) | (:REGISTERED_ADDRESS {true} ) | (:INTERMEDIARY_OF {true} ))/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))*"

Q51 = "DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))+"
Q52 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))+"
Q53 = "DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?q - ?p <= 0.7})/ ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?q - ?p <= 0.7}))+"
Q54 = "DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until })/ ((:OFFICER_OF {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 < ?p }))+"
Q55 = """DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ ((:OFFICER_OF {true} )/ 
(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))+"""

Q61 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?/ 
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?
      
      """

Q62 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))?/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id}))?
"""

Q63 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))?/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))?
"""

Q64 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF  {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))?/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))?
"""

Q65 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                ((:OFFICER_OF  {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))?/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))?
"""

Q71 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/
                (((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))| 
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {node_id - ?p > 0.3 and ?p - node_id < 0.3})))
      
      """

Q72 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))/
                (((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id})))
"""

Q73 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})/ 
                ((:OFFICER_OF{true} )/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))/
                (((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7 }))|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})))
"""

Q74 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF{true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                (((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p }))|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p})))
"""

Q75 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                ((:OFFICER_OF{true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                (((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})))
"""



Q81 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?/
                 ((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?/ 
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?
      
      """

Q82 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id}))?
"""

Q83 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))?
"""

Q84 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF  {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))?
"""

Q85 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                ((:OFFICER_OF  {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))?/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))?
"""



Q91 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                (((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*)| 
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {node_id - ?p > 0.3 and ?p - node_id < 0.3}))
      
      """

Q92 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                (((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))*)|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id}))
"""

Q93 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7})/ 
                (((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))*)|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))
"""

Q94 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                (((:OFFICER_OF  {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))*)|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))
"""

Q95 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                (((:OFFICER_OF  {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))*)|
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))?
"""

Q101 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))?
      
      """

Q102 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))?
"""

Q103 =  """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p - ?q  <= 0.7}))?
"""

Q104 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))?
"""

Q105 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 })/ 
                ((:OFFICER_OF {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))*/
                 ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1 }))?
"""


Q111 =  """
        DATA_TEST NAIVE ?e (Officer {node_id - ?p > 0.3 and ?p - node_id < 0.3})/ 
                ((:OFFICER_OF {true} )/(Entity {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/
                 ((:REGISTERED_ADDRESS {true} )/(Address {node_id - ?p > 0.3 and ?p - node_id < 0.3}))/ 
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {node_id - ?p > 0.3 and ?p - node_id < 0.3}))*
      
      """

Q112 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id}))*
"""

Q113 = """ 
       DATA_TEST NAIVE ?e (Officer {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7})/ 
                ((:OFFICER_OF {true} )/(Entity {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?p >= node_id and ?q <= node_id and ?p -?q <= 0.7}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?p >= node_id and ?q <= node_id and ?p - ?q <= 0.7}))*
"""

Q114 = """ 
       DATA_TEST NAIVE ?e (Officer {?p == node_id and ?q == valid_until})/ 
                ((:OFFICER_OF  {true} )/(Entity {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until <= 0.1 and valid_until - ?q <= 0.1 and 0.5 * node_id + 0.1 <= ?p}))*
"""

Q115 = """ 
       DATA_TEST NAIVE ?e (Officer {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1})/ 
                ((:OFFICER_OF  {true} )/(Entity {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                ((:REGISTERED_ADDRESS {true} )/(Address {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))/
                 ((:INTERMEDIARY_OF {true} )/(Intermediary {?q - valid_until + ?p - node_id <= 0.1 and valid_until - ?q + ?p - node_id <= 0.1 and valid_until - ?q + node_id - ?p <= 0.1 and ?q - valid_until + node_id - ?p <= 0.1}))*
"""


REGEX_TEMPLATE = [TEMPLATE_Q0, TEMPLATE_Q1, TEMPLATE_Q2, TEMPLATE_Q3, TEMPLATE_Q4, TEMPLATE_Q5, TEMPLATE_Q6, TEMPLATE_Q7, TEMPLATE_Q8, TEMPLATE_Q9, TEMPLATE_Q10, TEMPLATE_Q11]

RDPQ_TEMPLATE = [ [Q01, Q02, Q03, Q04, Q05],
                 [Q11, Q12, Q13, Q14, Q15], 
                 [Q21, Q22, Q23, Q24, Q25], 
                 [Q31, Q32, Q33, Q34, Q35], 
                 [Q41, Q42, Q43, Q44, Q45], 
                 [Q51, Q52, Q53, Q54, Q55], 
                 [Q61, Q62, Q63, Q64, Q65], 
                 [Q71, Q72, Q73, Q74, Q75], 
                 [Q81, Q82, Q83, Q84, Q85], 
                 [Q91, Q92, Q93, Q94, Q95], 
                 [Q101, Q102, Q103, Q104, Q105],
                 [Q111, Q112, Q113, Q114, Q115],
                 ]


def create_command(start_point: str, query: str):
    return f"Match ({start_point}) =[{query}] => (?to) \n Return * \n Limit 1"


def icij_graph_query():
 
    server = start_server(DBS_DIR / "paradise")

    candidate = []

    result = []
    query_res = []
    # dating query

    id = 0
    for template_index in range(12):
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
        result.append(("PARADISE", f"REGEX Q{template_index}", res_dating))
        query_res.append(("PARADISE", f"REGEX Q{template_index}", query_res_dating))

        rdpq_templates = RDPQ_TEMPLATE[template_index]
    
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
                     result.append(("PARADISE", f"RDPQ Q{template_index+1}{query_index}", res_money))
                     query_res.append(("PARADISE",f"RDPQ Q{template_index+1}{query_index}", query_res_money))
                     query_index = query_index + 1

    


   
        
    kill_server(server)
    write_pickle(ROOT_TEST_DIR / "result" / "icij_paradise_naive_statistic.pickle", result)
    write_pickle(ROOT_TEST_DIR / "result" / "icij_paradise_naive_result.pickle", query_res)