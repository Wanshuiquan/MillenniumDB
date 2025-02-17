import subprocess

from evaluating import cases as case
from evaluating import data_manipulate as manipulate
from evaluating import option as op
from evaluating import util as util

if __name__ == "__main__":
    # subprocess.run(["rm", "-r", "$evaluation/data/facebook"])
    # subprocess.run(["rm", "-r", "$evaluation/data/youtube"])

    # print("manipulate .qm files")
    # manipulate.initialize_youtube_graph()
    # print("create data bases")
    # util.create_db(op.DBS_DIR / "youtube.qm")
    # util.create_db(op.DBS_DIR / "facebook.qm")
    # print("query")
    # case.facebook_graph_query()
    # case.youtube_graph_query()
    case.pokec_graph_query()
    print("finish testing")
