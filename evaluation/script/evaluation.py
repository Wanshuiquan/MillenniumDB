
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

def print_experiment(dataset, algo):
      print(f"Now run the {algo} algorithm with {dataset} dataset")

def run_telecom():
        print_experiment("telecom", "optimized")
        util.clear_directory_recreate("telecom")
        telecom.telecom_graph_query()
        util.file_handler("telecom")


def run_telecom_naive():
        print_experiment("telecom", "naive")
        util.clear_directory_recreate("telecom-naive")
        telecom_naive.telecom_graph_query()
        util.file_handler("telecom-naive")


def run_ldbc10():
        print_experiment("ldbc10", "optimized")
        util.clear_directory_recreate("ldbc10")
        ldbc10.icij_graph_query()
        util.file_handler("ldbc10")

def run_ldbc10_naive():
        print_experiment("ldbc10", "naive")
        util.clear_directory_recreate("ldbc10-naive")
        ldbc10_naive.icij_graph_query()
        util.file_handler("ldbc10-naive")   

def run_ldbc01():
        print_experiment("ldbc01", "optimized")        
        util.clear_directory_recreate("ldbc01")
        ldbc01.icij_graph_query()
        util.file_handler("ldbc01")


def run_ldbc01_naive():
        print_experiment("ldbc01", "naive")
        util.clear_directory_recreate("ldbc01-naive")
        ldbc01_naive.icij_graph_query()
        util.file_handler("ldbc01-naive")

def run_pokec():
        print_experiment("pokec", "optimized")
        util.clear_directory_recreate("pokec")
        pokec.pokec_graph_query()
        util.file_handler("pokec")


def run_pokec_naive():
        print_experiment("pokec", "naive")
        util.clear_directory_recreate("pokec-naive")
        pokec_naive.pokec_graph_query()
        util.file_handler("pokec-naive")


def run_icijleak():
        print_experiment("icijleak", "optimized")
        util.clear_directory_recreate("icijleak")
        icijleak.icij_graph_query()
        util.file_handler("icijleak")


def run_icijleak_naive():
        print_experiment("icijleak", "naive")
        util.clear_directory_recreate("icijleak-naive")
        icijleak_naive.icij_graph_query()
        util.file_handler("icijleak-naive") 


def run_paradise():
        print_experiment("paradise", "optimized")
        util.clear_directory_recreate("paradise")
        paradise.icij_graph_query()
        util.file_handler("paradise")



def run_paradise_naive():
        print_experiment("paradise", "naive")
        util.clear_directory_recreate("paradise-naive")
        paradise_naive.icij_graph_query()
        util.file_handler("paradise-naive")



def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <parameter>")
        sys.exit(1)
    # Get the parameter (sys.argv[0] is the script name, sys.argv[1] is the first argument)
    # util.prepare()
    queries = sys.argv[1]
    algorithm = sys.argv[2]
    
    if queries == "telecom":
        if algorithm == "optimized":
            run_telecom()
        elif algorithm == "naive":
                run_telecom_naive()
        else:
            run_telecom()
            run_telecom_naive()
        
    elif queries == "ldbc10":
         if algorithm == "optimized":
               run_ldbc10()
         elif algorithm == "naive":
               run_ldbc10_naive()
         else:
               run_ldbc10()
               run_ldbc10_naive()


    elif queries == "ldbc01":
         if algorithm == "optimized":
               run_ldbc01()
         elif algorithm == "naive":
               run_ldbc01_naive()
         else:
               run_ldbc01()
               run_ldbc01_naive()

        
    elif queries == "pokec":
         if algorithm == "optimized":
               run_pokec()
         elif algorithm == "naive":
               run_pokec_naive()
         else:
               run_pokec()
               run_pokec_naive()

    elif queries == "icijleak":
         if algorithm == "optimized":
               run_icijleak()
         elif algorithm == "naive":
               run_icijleak_naive()
         else:
               run_icijleak()
               run_icijleak_naive()
    elif queries == "paradise":
         if algorithm == "optimized":
               run_paradise()
         elif algorithm == "naive":
               run_paradise_naive()
         else:
               run_paradise()
               run_paradise_naive()    
    elif queries == "all":
        if algorithm == "optimized":
            run_ldbc01()
            run_paradise()
            run_icijleak()
            run_pokec()
            run_ldbc10()
            run_telecom()
        elif algorithm == "naive":
            run_ldbc01_naive()
            run_paradise_naive()
            run_icijleak_naive()
            run_pokec_naive()
            run_ldbc10_naive()
            run_telecom_naive()
        else:
            run_ldbc01()
            run_paradise()
            run_icijleak()
            run_pokec()
            run_ldbc10()
            run_telecom()
            run_ldbc01_naive()
            run_paradise_naive()
            run_icijleak_naive()
            run_pokec_naive()
            run_ldbc10_naive()
            run_telecom_naive()
    else:
        print(f"Unknown parameter: {queries}")
        sys.exit(1)

if __name__ == "__main__":
    main()