import pickle
import time
import psutil
import os

PROCESS_NAME = "mdb-server"
LOG_FILE = "memory.log"
CHECK_INTERVAL = 5  



def monitor_memory():
    logs = []

    while True:
        pid, rss, vms = get_process_memory(PROCESS_NAME)
        if pid: 
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} PID: {pid}, RSS: {rss / 1024 / 1024:.2f} MB, VMS: {vms / 1024 / 1024:.2f} MB\n"
            logs.append(log_entry)
            break
    while True:
        pid, rss, vms = get_process_memory(PROCESS_NAME)
        if pid:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} PID: {pid}, RSS: {rss / 1024 / 1024:.2f} MB, VMS: {vms / 1024 / 1024:.2f} MB\n"
            logs.append(log_entry)
        else:
            break
    with open("evaluation/result/mem.pkl", "wb") as fb:
                pickle.dump(logs, fb)
                


def get_process_memory(process_name=PROCESS_NAME):
    for proc in psutil.process_iter(attrs=['pid', 'name', 'memory_info']):
        if proc.info['name'] == process_name:
            return proc.info['pid'], proc.info['memory_info'].rss, proc.info['memory_info'].vms
    return None, None, None