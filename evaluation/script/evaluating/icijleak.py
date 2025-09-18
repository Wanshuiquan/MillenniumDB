import pickle
import sys
import time
import random
from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR

from .util import execute_query, kill_server, sample, send_query, start_server, get_mdb_server_memory
from .query import create_query_command


ICIJ_LEAK_SAMPLE = 100
ICIJ_SIZE = 1908466
"""
A = Entity / same_as 
B = Officier / DIRECTOR_OF 
C = Intermediary / SHAREHOLDER_OF
"""
TEMPLATE_Q0 = "ANY SIMPLE ?e (:same_as | :same_name_as | underlying)* "
TEMPLATE_Q1 =  "ANY SIMPLE ?e :same_as*" 
TEMPLATE_Q2 = "ANY SIMPLE ?e :same_as/:same_name_as/underlying"
TEMPLATE_Q3 = "ANY SIMPLE ?e :same_as*/:same_name_as"
TEMPLATE_Q4 = "ANY SIMPLE ?e (:same_as | :same_name_as | underlying) "
TEMPLATE_Q5 =  "ANY SIMPLE ?e :same_as+" 
TEMPLATE_Q6 = "ANY SIMPLE ?e :same_as?/:same_name_as?/underlying?"
TEMPLATE_Q7 = "ANY SIMPLE ?e :same_as/(:same_name_as | underlying)"
TEMPLATE_Q8 = "ANY SIMPLE ?e :same_as/:same_name_as?/underlying?"
TEMPLATE_Q9 = "ANY SIMPLE ?e (:same_as/:same_name_as*)|underlying"
TEMPLATE_Q10 = "ANY SIMPLE ?e :same_as?/:same_name_as*"
TEMPLATE_Q11 = "ANY SIMPLE ?e :same_as/:same_name_as/underlying*"

Q01 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/((underlying {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q02 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))/(underlying {true} )/((Entity {?p >= valid_until and ?q <= valid_until}))*"
Q03 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ (((:same_as {true}) | (:same_name_as {true} ) | (:underlying {true} ))/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*"
Q04 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q == node_id})/ (((:same_as {true}) | (:same_name_as {true} ) | (:underlying {true} ))/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*"
Q05 = "DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ ((((:same_as {true}) | (:same_name_as {true} ) | (:underlying {true} ))/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})))*"


Q11 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q12 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*"
Q13 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7})/ ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7}))*"
Q14 = "DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id })/ ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p }))*"
Q15 = """DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ ((:same_as {true} )/ 
(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*"""

Q21 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q22 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))
"""


Q23 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
                 ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))
"""

Q24 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                 ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))
"""

Q25 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:same_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                 ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))"""


Q31 = """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/
                 ((:same_name_as {valid_until - ?p > 15 and ?p - valid_until < 15} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q32 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {?p >= valid_until and ?q <= valid_until} )/(Entity {?p >= valid_until and ?q <= valid_until}))*/
                 ((:same_name_as {?p >= valid_until and ?q <= valid_until} )/(Entity {?p >= valid_until and ?q <= valid_until}))
"""



Q33 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))*/
                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))
"""


Q34 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p}))*/
                 ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p}))
"""

Q35 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:same_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*/
                 ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))
"""



Q41 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15 })/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*"
Q42 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ (((:same_as {true}) | (:same_name_as {true} ) | (underlying {true} ))/(Entity {?p >= valid_until and ?q <= valid_until}))*"
Q43 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ (((:same_as {true}) | (:same_name_as {true} ) | (:underlying {true} ))/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*"
Q44 = "DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ (((:same_as {true}) | (:same_name_as {true} ) | (:underlying {true} ))/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*"
Q45 = "DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ (((:same_as {true}) | (:same_name_as {true} ) | (:underlying {true} ))/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))*"

Q51 = "DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))+"
Q52 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))+"
Q53 = "DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7})/ ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?q - ?p <= 7}))+"
Q54 = "DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id })/ ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 < ?p }))+"
Q55 = """DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ ((:same_as {true} )/ 
(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))+"""

Q61 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))?/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))?/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))?
      
      """

Q62 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))?
"""

Q63 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))?/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))?/
                 ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))?
"""

Q64 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as  {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?/
                ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?/
                 ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?
"""

Q65 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:same_as  {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))?/
                ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))?/
                 ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))?
"""

Q71 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                (((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))| 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15})))
      
      """

Q72 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                (((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))|
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until})))
"""

Q73 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:same_as{true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
                (((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7 }))|
                 ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})))
"""

Q74 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as{true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                (((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p }))|
                 ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p})))
"""

Q75 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:same_as{true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                (((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))|
                 ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})))
"""



Q81 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))?/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))?/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))?
      
      """

Q82 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))?
"""

Q83 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))?/
                 ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))?
"""

Q84 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as  {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?/
                 ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?
"""

Q85 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:same_as  {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))?/
                 ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))?
"""



Q91 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                (((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*)| 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
      """

Q92 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                (((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*)|
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))
"""

Q93 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
                (((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))*)|
                 ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))
"""

Q94 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                (((:same_as  {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*)|
                 ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))
"""

Q95 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                (((:same_as  {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))*)|
                 ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))?
"""

Q101 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))?
      
      """

Q102 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*/
                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?
"""

Q103 =  """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*/
                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))?
"""

Q104 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*/
                 ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?
"""

Q105 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 })/ 
                ((:same_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*/
                 ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))?
"""


Q111 =  """
        DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
                ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
                 ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/ 
                 ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
      """

Q112 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
                 ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))*
"""

Q113 = """ 
       DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
                ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))/
                ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))/
                 ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))*
"""

Q114 = """ 
       DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
                ((:same_as  {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
                 ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*
"""

Q115 = """ 
       DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
                ((:same_as  {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
                 ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))*
"""

# Q41 =  """
#         DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
#                 ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
#                  ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
#       """

# Q42 = """ 
#        DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
#                 ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
#                  ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))
# """

# Q43 = """ 
#        DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7})/ 
#                 ((:same_as {true} )/(Entity {?p >= valid_until and ?p - ?q <= 7}))/
#                  ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p -?q <= 7}))
# """

# Q44 = """ 
#        DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
#                 ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id -?q <= 100 and  0.5 * valid_until + 100 <= ?p}))/
#                  ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id -?q <= 100 and  0.5 * valid_until + 100 <= ?p}))
# """

# Q45 = """ 
#        DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
#                 ((:same_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
#                  ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))
# """

# Q51 =  """
#         DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
#                 ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/
#                  ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*
      
#       """

# Q52 = """ 
#        DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
#                 ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))?/
#                  ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*
# """

# Q53 =  """ 
#        DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
#                 ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))?/
#                  ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q  <= 7}))*
# """

# Q54 = """ 
#        DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
#                 ((:same_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))?/
#                  ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))*
# """

# Q55 = """ 
#        DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 })/ 
#                 ((:same_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))?/
#                  ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*
# """




# Q71 =  """
#         DATA_TEST ?e (Entity {valid_until - ?p > 15 and ?p - valid_until < 15})/ 
#                 ((:same_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))/
#                  ((:same_name_as {true} )/(Entity {valid_until - ?p > 15 and ?p - valid_until < 15}))*/ 
#                  ((underlying {true} )/(Intermediary {valid_until - ?p > 15 and ?p - valid_until < 15}))
      
#       """

# Q72 = """ 
#        DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until})/ 
#                 ((:same_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))/
#                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until}))*/
#                  ((underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until}))
# """

# Q73 = """ 
#        DATA_TEST ?e (Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7})/ 
#                 ((:same_as{true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))/
#                 ((:same_name_as {true} )/(Entity {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7 }))*/
#                  ((:underlying {true} )/(Intermediary {?p >= valid_until and ?q <= valid_until and ?p - ?q <= 7}))
# """

# Q74 = """ 
#        DATA_TEST ?e (Entity {?p == valid_until and ?q == node_id})/ 
#                 ((:same_as{true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))/
#                 ((:same_name_as {true} )/(Entity {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p }))*/
#                  ((:underlying {true} )/(Intermediary {?q - node_id <= 100 and node_id - ?q <= 100 and 0.5 * valid_until + 100 <= ?p}))
# """

# Q75 = """ 
#        DATA_TEST ?e (Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100})/ 
#                 ((:same_as{true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))/
#                 ((:same_name_as {true} )/(Entity {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100 }))*/
#                  ((:underlying {true} )/(Intermediary {?q - node_id + ?p - valid_until <= 100 and node_id - ?q + ?p - valid_until <= 100 and node_id - ?q + valid_until - ?p <= 100 and ?q - node_id + valid_until - ?p <= 100}))
# """






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
 
#     candidate = send_query("""MATCH (?from)=[DATA_TEST ?e (Entity {valid_until - ?p > 50 and ?p - valid_until < 50})/ ((:same_as {true} )/(Entity {valid_until - ?p > 50 and ?p - valid_until < 50}))*]=>(?to)
# RETURN ?from
# LIMIT 2000""").split("\n")[1:-1]
    candidate = []
#     sample2 = send_query(f"Match (?x:Entity) =[:same_as*]=>(?y:Entity) Return ?x Limit 1000000").split("\n")[1:-1]
#     for i in candidate_index:
#         candidate.append(sample2[i])
    result = []
    query_res = []
    # dating query
    
    id = 0

    for template_index in range(12):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        memory = []
        candidate= sample(ICIJ_LEAK_SAMPLE, ICIJ_SIZE)
        server = start_server(DBS_DIR / "icij-leak")

        for index in candidate:
            sys.stdout.write(f"\rREGEX Q{template_index+1}" + str(id))
            sys.stdout.flush()
            id = id + 1
            query = create_query_command(str(index), regex_template)
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_dating.append((end_time - start_time) / 1000000)
            mem = get_mdb_server_memory()
            memory.append(mem)
            query_res_dating.append(query_result)
        kill_server(server)
        result.append(("POKEC", f"REGEX Q{template_index}", res_dating, memory))
        query_res.append(("POKEC", f"REGEX Q{template_index}", query_res_dating))
       
        rdpq_templates = RDPQ_TEMPLATE[template_index]
    
        query_index = 1

        for query in rdpq_templates:
              # money query 
                     res_money = []
                     query_res_money = []
                     memory = []
                     id = 0
                     server = start_server(DBS_DIR / "icij-leak")
   
                     for index in candidate:
                            sys.stdout.write(f"\rRDPQ Q{template_index}{query_index}  " + str(id))
                            sys.stdout.flush()
                            id = id + 1
                            query_command = create_query_command(str(index), query)
                            start_time = time.time_ns()
                            query_result = send_query(query_command)
                            end_time = time.time_ns()
                            res_money.append((end_time - start_time) / 1000000)
                            mem = get_mdb_server_memory()
                            memory.append(mem)
                            query_res_money.append(query_result)
                     kill_server(server)
                     result.append(("POKEC", f"RDPQ Q{template_index+1}{query_index}", res_money, memory))
                     query_res.append(("POKEC",f"RDPQ Q{template_index+1}{query_index}", query_res_money))
                     query_index = query_index + 1

    


   
        
    kill_server(server)
    with open(ROOT_TEST_DIR / "result" / "icij_leak_statistic.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "icij_leak_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)