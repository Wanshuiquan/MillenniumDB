import json
import sys
import time

from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR
from .query import create_query_command
from .util import execute_query, kill_server, sample, send_query, start_server, write_csv
import random

TELECOM_SAMPLE = 100
TELECOM_SIZE= 170000

"""
A = cell / lived 
B = Officier / DIRECTOR_OF 
C = Intermediary / SHAREHOLDER_OF
"""


TEMPLATE_Q0 = "ANY SIMPLE ?e (:lived | :used | bought)* "
TEMPLATE_Q1 =  "ANY SIMPLE ?e :lived*" 
TEMPLATE_Q2 = "ANY SIMPLE ?e :lived/:used/bought"
TEMPLATE_Q3 = "ANY SIMPLE ?e :lived*/:used"
TEMPLATE_Q4 = "ANY SIMPLE ?e (:lived | :used | bought) "
TEMPLATE_Q5 =  "ANY SIMPLE ?e :lived+" 
TEMPLATE_Q6 = "ANY SIMPLE ?e :lived?/:used?/bought?"
TEMPLATE_Q7 = "ANY SIMPLE ?e :lived/(:used | bought)"
TEMPLATE_Q8 = "ANY SIMPLE ?e :lived/:used?/bought?"
TEMPLATE_Q9 = "ANY SIMPLE ?e (:lived/:used*)|bought"
TEMPLATE_Q10 = "ANY SIMPLE ?e :lived?/:used*"
TEMPLATE_Q11 = "ANY SIMPLE ?e :lived/:used/bought*"

Q01 = "DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ (((:lived {true}) | (:used {true} ) | (bought {true} ))/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/((bought {true} )/(cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*"
Q02 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ (((:lived {true}) | (:used {true} ) | (bought {true} ))/(user {?p >= attr1 and ?q <= attr1}))/(bought {true} )/((cell {?p >= attr1 and ?q <= attr1}))*"
Q03 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})/ (((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))*"
Q04 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q == attr2})/ (((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))*"
Q05 = "DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ ((((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})))*"


Q11 = "DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*"
Q12 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))*"
Q13 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?q - ?p <= 0.7})/ ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?q - ?p <= 0.7}))*"
Q14 = "DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2 })/ ((:lived {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 < ?p }))*"
Q15 = """DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ ((:lived {true} )/ 
(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))*"""

Q21 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/
                 ((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/ 
                 ((:bought {true} )/(package {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))
      
      """

Q22 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1}))
"""


Q23 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1 and ?p - ?q  <= 0.7}))
"""

Q24 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                 ((:bought {true} )/(package {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))
"""

Q25 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                ((:lived {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                 ((:bought {true} )/(package {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))"""


Q31 = """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {attr1 - ?p > 0.3 and ?p - attr1 < 0.3} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*/
                 ((:used {attr1 - ?p > 0.3 and ?p - attr1 < 0.3} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))
      
      """

Q32 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {?p >= attr1 and ?q <= attr1} )/(user {?p >= attr1 and ?q <= attr1}))*/
                 ((:used {?p >= attr1 and ?q <= attr1} )/(app {?p >= attr1 and ?q <= attr1}))
"""



Q33 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p - ?q  <= 0.7}))*/
                 ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))
"""


Q34 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 < ?p}))*/
                 ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 < ?p}))
"""

Q35 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                ((:lived {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))*/
                 ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))
"""



Q41 = "DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3 })/ (((:lived {true}) | (:used {true} ) | (bought {true} ))/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*"
Q42 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ (((:lived {true}) | (:used {true} ) | (bought {true} ))/(user {?p >= attr1 and ?q <= attr1}))*"
Q43 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})/ (((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))*"
Q44 = "DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ (((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))*"
Q45 = "DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ (((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))*"

Q51 = "DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))+"
Q52 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))+"
Q53 = "DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?q - ?p <= 0.7})/ ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?q - ?p <= 0.7}))+"
Q54 = "DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2 })/ ((:lived {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 < ?p }))+"
Q55 = """DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ ((:lived {true} )/ 
(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))+"""

Q61 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?/
                 ((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?/ 
                 ((:bought {true} )/(package {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?
      
      """

Q62 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))?/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))?/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1}))?
"""

Q63 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))?/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))?/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))?
"""

Q64 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived  {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))?/
                ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))?/
                 ((:bought {true} )/(package {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))?
"""

Q65 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                ((:lived  {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))?/
                ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))?/
                 ((:bought {true} )/(package {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))?
"""

Q71 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/
                (((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))| 
                 ((:bought {true} )/(package {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})))
      
      """

Q72 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))/
                (((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))|
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1})))
"""

Q73 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})/ 
                ((:lived{true} )/(user {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))/
                (((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7 }))|
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})))
"""

Q74 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived{true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                (((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p }))|
                 ((:bought {true} )/(package {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p})))
"""

Q75 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                ((:lived{true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                (((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))|
                 ((:bought {true} )/(package {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})))
"""



Q81 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?/
                 ((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?/ 
                 ((bought {true} )/(package {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?
      
      """

Q82 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))?/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1}))?
"""

Q83 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))?/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))?
"""

Q84 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived  {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))?/
                 ((:bought {true} )/(package {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))?
"""

Q85 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                ((:lived  {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))?/
                 ((:bought {true} )/(package {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))?
"""



Q91 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                (((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/
                 ((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*)| 
                 ((bought {true} )/(package {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))
      
      """

Q92 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                (((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))*)|
                 ((bought {true} )/(package {?p >= attr1 and ?q <= attr1}))
"""

Q93 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7})/ 
                (((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))*)|
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))
"""

Q94 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                (((:lived  {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))*)|
                 ((:bought {true} )/(package {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))
"""

Q95 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                (((:lived  {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))*)|
                 ((:bought {true} )/(package {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))?
"""

Q101 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*/
                 ((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))?
      
      """

Q102 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))*/
                 ((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))?
"""

Q103 =  """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))*/
                 ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p - ?q  <= 0.7}))?
"""

Q104 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))*/
                 ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))?
"""

Q105 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 })/ 
                ((:lived {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))*/
                 ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1 }))?
"""


Q111 =  """
        DATA_TEST NAIVE ?e (cell {attr1 - ?p > 0.3 and ?p - attr1 < 0.3})/ 
                ((:lived {true} )/(user {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/
                 ((:used {true} )/(app {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))/ 
                 ((:bought {true} )/(package {attr1 - ?p > 0.3 and ?p - attr1 < 0.3}))*
      
      """

Q112 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1}))/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1}))*
"""

Q113 = """ 
       DATA_TEST NAIVE ?e (cell {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7})/ 
                ((:lived {true} )/(user {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))/
                ((:used {true} )/(app {?p >= attr1 and ?q <= attr1 and ?p -?q <= 0.7}))/
                 ((:bought {true} )/(package {?p >= attr1 and ?q <= attr1 and ?p - ?q <= 0.7}))*
"""

Q114 = """ 
       DATA_TEST NAIVE ?e (cell {?p == attr1 and ?q == attr2})/ 
                ((:lived  {true} )/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                ((:used {true} )/(app {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))/
                 ((:bought {true} )/(package {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))*
"""

Q115 = """ 
       DATA_TEST NAIVE ?e (cell {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1})/ 
                ((:lived  {true} )/(user {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                ((:used {true} )/(app {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))/
                 ((:bought {true} )/(package {?q - attr2 + ?p - attr1 <= 0.1 and attr2 - ?q + ?p - attr1 <= 0.1 and attr2 - ?q + attr1 - ?p <= 0.1 and ?q - attr2 + attr1 - ?p <= 0.1}))*
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


def telecom_graph_query():
    server = start_server(DBS_DIR / "telecom", timeout=30)
    result = []
    query_res = []
    # dating query

    attr1 = 0
    for template_index in range(12):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        candattr1ate = sample(100, TELECOM_SIZE)

        for index in candattr1ate:
            sys.stdout.write(f"\rREGEX Q{template_index+1}" + str(attr1))
            sys.stdout.flush()
            attr1 = attr1 + 1

            query = create_query_command(str(index), regex_template)
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_dating.append((end_time - start_time) / 1000000)
            query_res_dating.append(query_result)
        result.append(("TELECOKOM", f"REGEX Q{template_index}", res_dating))
        query_res.append(("TELECOKOM", f"REGEX Q{template_index}", query_res_dating))

        rdpq_templates = RDPQ_TEMPLATE[template_index]
    
        query_index = 1

        for query in rdpq_templates:
              # money query 
                     res_money = []
                     query_res_money = []
                     attr1 = 0
                     for index in candattr1ate:
                            sys.stdout.write(f"\rRDPQ Q{template_index+1}{query_index}  " + str(attr1))
                            sys.stdout.flush()
                            attr1 = attr1 + 1
                            query_command = create_query_command(str(index), query)
                            start_time = time.time_ns()
                            query_result = send_query(query_command)
                            end_time = time.time_ns()
                            print(query_command)
                            res_money.append((end_time - start_time) / 1000000)
                            query_res_money.append(query_result)
                     result.append(("TELECOKOM", f"RDPQ Q{template_index+1}{query_index}", res_money))
                     query_res.append(("TELECOKOM",f"RDPQ Q{template_index+1}{query_index}", query_res_money))
                     query_index = query_index + 1

    


   
        
    kill_server(server)
    write_csv(ROOT_TEST_DIR / "result" / "telecom_naive_statistic.csv", result)
    write_csv(ROOT_TEST_DIR / "result" / "telecom_naive_result.csv", query_res)

