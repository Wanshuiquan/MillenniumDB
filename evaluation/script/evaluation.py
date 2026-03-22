
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

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <parameter>")
        sys.exit(1)
    # Get the parameter (sys.argv[0] is the script name, sys.argv[1] is the first argument)
    util.prepare()
    queries = sys.argv[1]

    
    if queries == "telecom":
        telecom.telecom_graph_query()
        util.file_handler("telecom")
        telecom_naive.telecom_graph_query()
        util.file_handler("telecom-naive")
        
    elif queries == "ldbc10":
        ldbc10.icij_graph_query()
        util.file_handler("ldbc10")

        ldbc10_naive.icij_graph_query()
        util.file_handler("ldbc10-naive")
    elif queries == "ldbc01":
        ldbc01.icij_graph_query()
        util.file_handler("ldbc01")
        ldbc01_naive.icij_graph_query()
        util.file_handler("ldbc01-naive")
    elif queries == "pokec":
        pokec.pokec_graph_query()
        util.file_handler("pokec")
        pokec_naive.pokec_graph_query()
        util.file_handler("pokec-naive")
    elif queries == "icijleak":
        icijleak.icij_graph_query()
        util.file_handler("icijleak")
        icijleak_naive.icij_graph_query()
        util.file_handler("icijleak-naive")
    elif queries == "paradise":
        paradise.icij_graph_query()
        util.file_handler("paradise")
        paradise_naive.icij_graph_query()
        util.file_handler("paradise-naive")
    elif queries == "all":
        telecom.telecom_graph_query()
        util.file_handler("telecom")
        telecom_naive.telecom_graph_query()
        util.file_handler("telecom-naive")
        ldbc10.icij_graph_query()
        util.file_handler("ldbc10")
        ldbc10_naive.icij_graph_query()
        util.file_handler("ldbc10-naive")
        ldbc01.icij_graph_query()
        util.file_handler("ldbc01")
        ldbc01_naive.icij_graph_query()
        util.file_handler("ldbc01-naive")
        pokec.pokec_graph_query()
        util.file_handler("pokec")
        pokec_naive.pokec_graph_query()
        util.file_handler("pokec-naive")
        icijleak.icij_graph_query()
        util.file_handler("icijleak")
        icijleak_naive.icij_graph_query()
        util.file_handler("icijleak-naive")
        paradise.icij_graph_query()
        util.file_handler("paradise")
        paradise_naive.icij_graph_query()
        util.file_handler("paradise-naive")
    else:
        print(f"Unknown parameter: {queries}")
        sys.exit(1)

if __name__ == "__main__":
    main()