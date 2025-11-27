
from evaluating import (
    telecom_naive, 
    telecom, 
    ldbc10, 
    ldbc10_naive, 
    ldbc01, 
    ldbc01_naive, 
    pokec,
    pokec_naive,
    icijleak,
    icijleak_naive,
    paradise,
    paradise_naive,
    util 
)
import sys 

def run_telecom():
        util.clear_directory_recreate("telecom")
        telecom.telecom_graph_query()
        util.file_handler("telecom")
        util.clear_directory_recreate("telecom-naive")
        telecom_naive.telecom_graph_query()
        util.file_handler("telecom-naive")

def run_ldbc10():
        util.clear_directory_recreate("ldbc10")
        ldbc10.icij_graph_query()
        util.file_handler("ldbc10")
        util.clear_directory_recreate("ldbc10-naive")
        ldbc10_naive.icij_graph_query()
        util.file_handler("ldbc10-naive")    

def run_ldbc01():
        util.clear_directory_recreate("ldbc01")
        ldbc01.icij_graph_query()
        util.file_handler("ldbc01")
        util.clear_directory_recreate("ldbc01-naive")
        ldbc01_naive.icij_graph_query()
        util.file_handler("ldbc01-naive")

def run_pokec():
        util.clear_directory_recreate("pokec")
        pokec.pokec_graph_query()
        util.file_handler("pokec")
        util.clear_directory_recreate("pokec-naive")
        pokec_naive.pokec_graph_query()
        util.file_handler("pokec-naive")

def run_icijleak():
        util.clear_directory_recreate("icijleak")
        icijleak.icij_graph_query()
        util.file_handler("icijleak")
        util.clear_directory_recreate("icijleak-naive")
        icijleak_naive.icij_graph_query()
        util.file_handler("icijleak-naive")

def run_paradise():
        util.clear_directory_recreate("paradise")
        paradise.icij_graph_query()
        util.file_handler("paradise")
        util.clear_directory_recreate("paradise-naive")
        paradise_naive.icij_graph_query()
        util.file_handler("paradise-naive")
def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <parameter>")
        sys.exit(1)
    # Get the parameter (sys.argv[0] is the script name, sys.argv[1] is the first argument)
    # util.prepare()
    queries = sys.argv[1]

    
    if queries == "telecom":
        run_telecom()
        
    elif queries == "ldbc10":
         run_ldbc10()


    elif queries == "ldbc01":
        run_ldbc01()

    elif queries == "pokec":
        run_pokec()

    elif queries == "icijleak":
        run_icijleak()
    elif queries == "paradise":
        run_paradise()
    elif queries == "all":
        run_ldbc01()
        run_paradise()
        run_icijleak()
        run_pokec()
        run_ldbc10()
        run_telecom()
    else:
        print(f"Unknown parameter: {queries}")
        sys.exit(1)

if __name__ == "__main__":
    main()