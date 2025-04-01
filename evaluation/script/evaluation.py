from evaluating import icijleak,pokec
from evaluating import option as op
from evaluating import util as util
from evaluating import performance_monitoring
import threading
import subprocess

def monitor_mem():
    subprocess.Popen("./monitor.sh",shell=True)
if __name__ == "__main__":
    mdb_thread = threading.Thread(target=pokec.pokec_graph_query, daemon=True)
    mdb_thread.start()

    monitor_thread = threading.Thread(target=performance_monitoring.monitor_memory, daemon=True)
    monitor_thread.start()

    mdb_thread.join()
    monitor_thread.join()
    print("finish testing")
