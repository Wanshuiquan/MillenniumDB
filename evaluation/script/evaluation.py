import sys

from evaluating import (
    icijleak,
    icijleak_naive,
    ldbc01,
    ldbc01_naive,
    ldbc10,
    ldbc10_naive,
    paradise,
    paradise_naive,
    pokec,
    pokec_naive,
    telecom,
    telecom_naive,
    util,
)


def run_queries(query_name, opti, naive):
    if query_name == "telecom":
        if opti:
            util.prepare("telecom", "optimized")
            telecom.telecom_graph_query()
        if naive:
            util.prepare("telecom", "naive")
            telecom_naive.telecom_graph_query()
    elif query_name == "ldbc10":
        if opti:
            util.prepare("ldbc10", "optimized")
            ldbc10.icij_graph_query()
        if naive:
            util.prepare("ldbc10", "naive")
            ldbc10_naive.icij_graph_query()
    elif query_name == "ldbc01":
        if opti:
            util.prepare("ldbc01", "optimized")
            ldbc01.icij_graph_query()
        if naive:
            util.prepare("ldbc01", "naive")
            ldbc01_naive.icij_graph_query()
    elif query_name == "pokec":
        if opti:
            util.prepare("pokec", "optimized")
            pokec.pokec_graph_query()
        if naive:
            util.prepare("pokec", "naive")
            pokec_naive.pokec_graph_query()
    elif query_name == "icijleak":
        if opti:
            util.prepare("icijleak", "optimized")
            icijleak.icij_graph_query()
        if naive:
            util.prepare("icijleak", "naive")
            icijleak_naive.icij_graph_query()
    elif query_name == "paradise":
        if opti:
            util.prepare("paradise", "optimized")
            paradise.icij_graph_query()
        if naive:
            util.prepare("paradise", "naive")
            paradise_naive.icij_graph_query()
    else:
        print(f"Unknown parameter: {query_name}")
        sys.exit(1)


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

    if queries == "all":
        for query_name in ["telecom", "ldbc10", "ldbc01", "pokec", "icijleak", "paradise"]:
            run_queries(query_name, opti, naive)
    else:
        run_queries(queries, opti, naive)


if __name__ == "__main__":
    main()
