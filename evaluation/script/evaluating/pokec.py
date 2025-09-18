import pickle
import sys
import time

from .option import DATA_DIR, DBS_DIR, FB_SIZE, ROOT_TEST_DIR, YOUTUBE_SIZE, POKEC_SIZE
from .query import create_query_command

from .util import execute_query, kill_server, sample, send_query, start_server,get_mdb_server_memory


POKEC_SAMPLE = 100

"""
A = Follow
B = Favorite 
C = FollowAnonymously
"""

TEMPLATE_Q0 = "ANY SIMPLE ?e (:Follow | :Favorite | Follow)* "
TEMPLATE_Q1 =  "ANY SIMPLE ?e :Follow*" 
TEMPLATE_Q2 = "ANY SIMPLE ?e :Follow/:Favorite/FollowAnonymously"
TEMPLATE_Q3 = "ANY SIMPLE ?e :Follow*/:Favorite"
TEMPLATE_Q4 = "ANY SIMPLE ?e (:Follow | :Favorite | FollowAnonymously) "
TEMPLATE_Q5 =  "ANY SIMPLE ?e :Follow+" 
TEMPLATE_Q6 = "ANY SIMPLE ?e :Follow?/:Favorite?/FollowAnonymously?"
TEMPLATE_Q7 = "ANY SIMPLE ?e :Follow/(:Favorite | FollowAnonymously)"
TEMPLATE_Q8 = "ANY SIMPLE ?e :Follow/:Favorite?/FollowAnonymously?"
TEMPLATE_Q9 = "ANY SIMPLE ?e (:Follow/:Favorite*)|FollowAnonymously"
TEMPLATE_Q10 = "ANY SIMPLE ?e :Follow?/:Favorite*"
TEMPLATE_Q11 = "ANY SIMPLE ?e :Follow/:Favorite/FollowAnonymously*"

Q01 = "DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ (((:Follow {true}) | (:Favorite {true} ) | (FollowAnonymously {true} ))/(people {AGE - ?p > 15 and ?p - AGE < 15}))/((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))*"
Q02 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ (((:Follow {true}) | (:Favorite {true} ) | (FollowAnonymously {true} ))/(people {?p >= AGE and ?q <= AGE}))/(FollowAnonymously {true} )/((people {?p >= AGE and ?q <= AGE}))*"
Q03 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})/ (((:Follow {true}) | (:Favorite {true} ) | (:FollowAnonymously {true} ))/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))*"
Q04 = "DATA_TEST ?e (people {?p >= AGE and ?q == completion_percentage})/ (((:Follow {true}) | (:Favorite {true} ) | (:FollowAnonymously {true} ))/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))*"
Q05 = "DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ ((((:Follow {true}) | (:Favorite {true} ) | (:FollowAnonymously {true} ))/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})))*"


Q11 = "DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))*"
Q12 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))*"
Q13 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?q - ?p <= 7})/ ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?q - ?p <= 7}))*"
Q14 = "DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage })/ ((:Follow {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 < ?p }))*"
Q15 = """DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ ((:Follow {true} )/ 
(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))*"""

Q21 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))/
                 ((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))/ 
                 ((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))
      
      """

Q22 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))/
                 ((FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE}))
"""


Q23 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))/
                 ((:FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q  <= 7}))
"""

Q24 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))
"""

Q25 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                ((:Follow {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))"""


Q31 = """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {AGE - ?p > 15 and ?p - AGE < 15} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))*/
                 ((:Favorite {AGE - ?p > 15 and ?p - AGE < 15} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))
      
      """

Q32 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {?p >= AGE and ?q <= AGE} )/(people {?p >= AGE and ?q <= AGE}))*/
                 ((:Favorite {?p >= AGE and ?q <= AGE} )/(people {?p >= AGE and ?q <= AGE}))
"""



Q33 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q  <= 7}))*/
                 ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))
"""


Q34 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 < ?p}))*/
                 ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 < ?p}))
"""

Q35 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                ((:Follow {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))*/
                 ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))
"""



Q41 = "DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15 })/ (((:Follow {true}) | (:Favorite {true} ) | (FollowAnonymously {true} ))/(people {AGE - ?p > 15 and ?p - AGE < 15}))*"
Q42 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ (((:Follow {true}) | (:Favorite {true} ) | (FollowAnonymously {true} ))/(people {?p >= AGE and ?q <= AGE}))*"
Q43 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})/ (((:Follow {true}) | (:Favorite {true} ) | (:FollowAnonymously {true} ))/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))*"
Q44 = "DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ (((:Follow {true}) | (:Favorite {true} ) | (:FollowAnonymously {true} ))/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))*"
Q45 = "DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ (((:Follow {true}) | (:Favorite {true} ) | (:FollowAnonymously {true} ))/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))*"

Q51 = "DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))+"
Q52 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))+"
Q53 = "DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?q - ?p <= 7})/ ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?q - ?p <= 7}))+"
Q54 = "DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage })/ ((:Follow {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 < ?p }))+"
Q55 = """DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ ((:Follow {true} )/ 
(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))+"""

Q61 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?/
                 ((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?/ 
                 ((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?
      
      """

Q62 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))?/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))?/
                 ((FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE}))?
"""

Q63 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p -?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))?/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))?/
                 ((:FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))?
"""

Q64 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow  {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))?/
                ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))?/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))?
"""

Q65 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                ((:Follow  {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))?/
                ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))?/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))?
"""

Q71 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))/
                (((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))| 
                 ((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15})))
      
      """

Q72 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))/
                (((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))|
                 ((FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE})))
"""

Q73 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})/ 
                ((:Follow{true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))/
                (((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7 }))|
                 ((:FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})))
"""

Q74 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow{true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                (((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p }))|
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p})))
"""

Q75 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                ((:Follow{true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                (((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))|
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})))
"""



Q81 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?/
                 ((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?/ 
                 ((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?
      
      """

Q82 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))?/
                 ((FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE}))?
"""

Q83 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p -?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))?/
                 ((:FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))?
"""

Q84 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow  {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))?/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))?
"""

Q85 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                ((:Follow  {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))?/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))?
"""



Q91 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                (((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))/
                 ((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))*)| 
                 ((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))
      
      """

Q92 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                (((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))*)|
                 ((FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE}))
"""

Q93 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p -?q <= 7})/ 
                (((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))*)|
                 ((:FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))
"""

Q94 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                (((:Follow  {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))*)|
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))
"""

Q95 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                (((:Follow  {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))*)|
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))?
"""

Q101 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))*/
                 ((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))?
      
      """

Q102 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))*/
                 ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))?
"""

Q103 =  """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))*/
                 ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q  <= 7}))?
"""

Q104 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))*/
                 ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))?
"""

Q105 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 })/ 
                ((:Follow {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))*/
                 ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100 }))?
"""


Q111 =  """
        DATA_TEST ?e (people {AGE - ?p > 15 and ?p - AGE < 15})/ 
                ((:Follow {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))/
                 ((:Favorite {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))/ 
                 ((FollowAnonymously {true} )/(people {AGE - ?p > 15 and ?p - AGE < 15}))*
      
      """

Q112 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE}))/
                 ((FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE}))*
"""

Q113 = """ 
       DATA_TEST ?e (people {?p >= AGE and ?q <= AGE and ?p -?q <= 7})/ 
                ((:Follow {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))/
                ((:Favorite {true} )/(people {?p >= AGE and ?q <= AGE and ?p -?q <= 7}))/
                 ((:FollowAnonymously {true} )/(people {?p >= AGE and ?q <= AGE and ?p - ?q <= 7}))*
"""

Q114 = """ 
       DATA_TEST ?e (people {?p == AGE and ?q == completion_percentage})/ 
                ((:Follow  {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                ((:Favorite {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage <= 100 and completion_percentage - ?q <= 100 and 0.5 * AGE + 100 <= ?p}))*
"""

Q115 = """ 
       DATA_TEST ?e (people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100})/ 
                ((:Follow  {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                ((:Favorite {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))/
                 ((:FollowAnonymously {true} )/(people {?q - completion_percentage + ?p - AGE <= 100 and completion_percentage - ?q + ?p - AGE <= 100 and completion_percentage - ?q + AGE - ?p <= 100 and ?q - completion_percentage + AGE - ?p <= 100}))*
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



def pokec_graph_query():
    candAGEate = sample(POKEC_SAMPLE,POKEC_SIZE)
    result = []
    query_res = []
    # dating query
    memory = []

    AGE = 0
    for template_index in range(12):
        regex_template =  REGEX_TEMPLATE[template_index]
        res_dating = []
        query_res_dating = []
        server = start_server(DBS_DIR / "pokec")
        for index in candAGEate:
            sys.stdout.write(f"\rREGEX Q{template_index+1}" + str(AGE))
            sys.stdout.flush()
            AGE = AGE + 1
            query = create_query_command(str(index), regex_template)
            start_time = time.time_ns()
            query_result = send_query(query)
            end_time = time.time_ns()
            res_dating.append((end_time - start_time) / 1000000)
            query_res_dating.append(query_result)
            mem = get_mdb_server_memory()
            memory.append(mem)
        result.append(("POKEC", f"REGEX Q{template_index}", res_dating, memory))
        query_res.append(("POKEC", f"REGEX Q{template_index}", query_res_dating))
        kill_server(server)
        rdpq_templates = RDPQ_TEMPLATE[template_index]
    
        query_index = 1

        for query in rdpq_templates:
              # money query 
                     res_money = []
                     query_res_money = []
                     memory = []
                     AGE = 0
                     server = start_server(DBS_DIR / "pokec")
                     for index in candAGEate:
                            sys.stdout.write(f"\rRDPQ Q{template_index+1}{query_index}  " + str(AGE))
                            sys.stdout.flush()
                            AGE = AGE + 1
                            query_command = create_query_command(str(index), query)
                            start_time = time.time_ns()
                            query_result = send_query(query_command)
                            end_time = time.time_ns()
                            res_money.append((end_time - start_time) / 1000000)
                            query_res_money.append(query_result)
                            mem = get_mdb_server_memory()
                            memory.append(mem)
                     result.append(("POKEC", f"RDPQ Q{template_index+1}{query_index}", res_money, memory))
                     query_res.append(("POKEC",f"RDPQ Q{template_index+1}{query_index}", query_res_money))
                     kill_server(server)
                     query_index = query_index + 1

    


   
        
    kill_server(server)
    with open(ROOT_TEST_DIR / "result" / "pokec_statistic.pkl", "wb") as fb:
        pickle.dump(result, fb)

    with open(ROOT_TEST_DIR / "result" / "pokec_result.pkl", "wb") as fb:
        pickle.dump(query_res, fb)

