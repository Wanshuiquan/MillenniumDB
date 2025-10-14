from gdb import parameter
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
    paradise_naive 
)
import sys 

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <parameter>")
        sys.exit(1)
    
    # Get the parameter (sys.argv[0] is the script name, sys.argv[1] is the first argument)
    queries = sys.argv[1]
    if queries == "telecom":
        telecom.pokec_graph_query()
        telecom_naive.pokec_graph_query()
    elif queries == "ldbc10":
        ldbc10.icij_graph_query()
        ldbc10_naive.icij_graph_query()
    elif queries == "ldbc01":
        ldbc01.icij_graph_query()
        ldbc01_naive.icij_graph_query()
    elif queries == "pokec":
        pokec.pokec_graph_query()
        pokec_naive.pokec_graph_query()
    elif queries == "icijleak":
        icijleak.icij_graph_query()
        icijleak_naive.icij_graph_query()
    elif queries == "paradise":
        paradise.icij_graph_query()
        paradise_naive.icij_graph_query()
    elif queries == "all":
        telecom.pokec_graph_query()
        telecom_naive.pokec_graph_query()
        ldbc10.icij_graph_query()
        ldbc10_naive.icij_graph_query()
        ldbc01.icij_graph_query()
        ldbc01_naive.icij_graph_query()
        pokec.pokec_graph_query()
        pokec_naive.pokec_graph_query()
        icijleak.icij_graph_query()
        icijleak_naive.icij_graph_query()
        paradise.icij_graph_query()
        paradise_naive.icij_graph_query()
    else:
        print(f"Unknown parameter: {queries}")
        sys.exit(1)

if __name__ == "__main__":
    main()