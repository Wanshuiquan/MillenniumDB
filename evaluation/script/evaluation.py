
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
    if len(sys.argv) != 3:
        print("Usage: python script.py <parameter>")
        sys.exit(1)
    # Get the parameter (sys.argv[0] is the script name, sys.argv[1] is the first argument)
    queries = sys.argv[1]
    mode = sys.argv[2] 
    
    opti = False 
    naive = False 
    if mode in ["optimized", "both"]:
        opti = True
    if mode in ["naive", "both"]:
        naive = True

    if queries == "telecom" or queries == "all":
        
        if opti:
            util.prepare("telecom", "optimized")
            telecom.telecom_graph_query()
        if naive:
            util.prepare("telecom", "naive")
            telecom_naive.telecom_graph_query()
    elif queries == "ldbc10" or queries == "all":
        if opti:
            util.prepare("ldbc10", "optimized")

            ldbc10.icij_graph_query()
        if naive:
            util.prepare("ldbc10", "naive")
            ldbc10_naive.icij_graph_query()
    elif queries == "ldbc01" or queries == "all":
        if opti:
            util.prepare("ldbc01", "optimized")
            ldbc01.icij_graph_query()
        if naive:
            util.prepare("ldbc01", "naive")
            ldbc01_naive.icij_graph_query()
    elif queries == "pokec" or queries == "all":
        if opti:
            util.prepare("pokec", "optimized")
            pokec.pokec_graph_query()
        if naive:
            util.prepare("pokec", "naive")
            pokec_naive.pokec_graph_query()
    elif queries == "icijleak" or queries == "all":
        if opti:
            util.prepare("icijleak", "optimized")
            icijleak.icij_graph_query()
        if naive:
            util.prepare("icijleak", "naive")
            icijleak_naive.icij_graph_query()
    elif queries == "paradise" or queries == "all":
        if opti:
            util.prepare("paradise", "optimized")
            paradise.icij_graph_query()
        if naive:
            util.prepare("paradise", "naive")
            paradise_naive.icij_graph_query()
    
    else:
        print(f"Unknown parameter: {queries}")
        sys.exit(1)

if __name__ == "__main__":
    main()