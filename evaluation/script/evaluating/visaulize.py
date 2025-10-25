import json
from util import ROOT_TEST_DIR
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import re
Z3_LOG_PATHS = {
        "L1": ROOT_TEST_DIR/"ldbc10"/"z3_debug.log",
        "L0": ROOT_TEST_DIR/"ldbc01"/"z3_debug.log", 
        "PO": ROOT_TEST_DIR/"pokec"/"z3_debug.log",
        "TE": ROOT_TEST_DIR/"telecom"/"z3_debug.log",
        "IL": ROOT_TEST_DIR/"icij-leak"/"z3_debug.log",
        "IP": ROOT_TEST_DIR/"paradise"/"z3_debug.log"
    }

OPTIMIZED_PATHS = {"L1":ROOT_TEST_DIR/"ldbc01"/"ldbc01_statistic.json", 
         "L0":ROOT_TEST_DIR/"ldbc01"/"ldbc01_statistic.json", 
         "PO":ROOT_TEST_DIR/"pokec"/"pokec_statistic.json",
         "TE":ROOT_TEST_DIR/"telecom"/"telecom_statistic.json",
         "IL":ROOT_TEST_DIR/"icij-leak"/"icij_leak_statistic.json",
         "IP":ROOT_TEST_DIR/"paradise"/"icij_paradise_statistic.json"}

NAIVE_PATHS = {"L1":ROOT_TEST_DIR/"ldbc10-naive"/"ldbc10_naive_statistic.json", 
         "L0":ROOT_TEST_DIR/"ldbc01-naive"/"ldbc01_naive_statistic.json", 
         "PO":ROOT_TEST_DIR/"pokec-naive"/"pokec_naive_statistic.json",
         "TE":ROOT_TEST_DIR/"telecom-naive"/"telecom_naive_statistic.json",
         "IL":ROOT_TEST_DIR/"icij-leak-naive"/"icij_leak_naive_statistic.json",
         "IP":ROOT_TEST_DIR/"paradise-naive"/"icij_paradise_naive_statistic.json"}

DATASET_STAT ={
            "L1": (30000000, 178000000),
        "L0": (180000, 1500000), 
        "PO": (1600000, 30600000),
        "TE": (170000, 50000000),
        "IL": (1900000, 3200000),
        "IP": (163000, 364000)
}

DATA_COLOR=['white', 'grey']

REGULAR_COLOR = ['white', 'lightgrey', 'darkgrey']
def classify_queries():
    """Define query complexity classifications"""
    return {
        'frequently_regular': ['Q1', 'Q2', 'Q3', 'Q4'],
        'occasionally_regular': ['Q5', 'Q6', 'Q7'],
        'rarely_regular': ['Q8', 'Q9', 'Q10', 'Q11', 'Q12'],
        'simple_data': ['D1', 'D2'],
        'complex_data': ['D3', 'D4', 'D5']
    }


def slice_small_log(path):
    f = open(path, "rb+") 
    count = 0 
    res = []
    d = {}
    for qi in range(12):
        d[f"Q{qi+1}"] = {}
    for line in f:
        if "exploration_depth" in line.decode('utf-8'):
            res.append(int(line.decode('utf-8').split(":")[1].strip()))
    for i in range(12):
        for j in range(5):
            d[f"Q{i+1}"][f"D{j+1}"] = res[i*500 + j*100: i*500 + (j+1)*100]
    return d

def slice_memory_data(path):
    f = open(path, "r") 
    count = 0 
    res = []
    d = {}
    for qi in range(12):
        d[f"Q{qi+1}"] = {}
    for line in f:
        if "memory" in line:
            match = re.search(r"memory:\s*(\d+)\s*MB", line)
            if match:
                number = int(match.group(1))
                res.append(number)
    for i in range(12):
        for j in range(5):
            d[f"Q{i+1}"][f"D{j+1}"] = res[i*500 + j*100: i*500 + (j+1)*100]
    return d


def load_memory_data(path):
    """Load running time data from pickle file"""
    with open(path, "rb+") as f:
        data = json.loads(f.read())
    
    time_data = {}
    for i in range(12):  # Q1-Q12
        query_key = f"Q{i+1}"
        time_data[query_key] = {}
        id = 0
        for dtype in ["RPQ", "D1", "D2", "D3", "D4", "D5"]:
            values = list(map(lambda x: x, data[i*6 + id][3]))
            time_data[query_key][dtype] = values    
            id = id + 1
    return time_data


def load_running_time_data(path, dataset_name):
    """Load running time data from pickle file"""
    with open(path, "rb+") as f:
        data = json.loads(f.read())
    
    time_data = {}
    for i in range(12):  # Q1-Q12
        query_key = f"Q{i+1}"
        time_data[query_key] = {}
        
        id = 0
        for dtype in ["RPQ", "D1", "D2", "D3", "D4", "D5"]:
            if id == 0:  # Skip RPQ
                id += 1
                continue
            values = list(map(lambda x: x, data[i*6 + id][2]))
            time_data[query_key][dtype] = values
            id += 1
    
    return time_data

def load_running_time(path, dataset_name):
        """Load running time data from pickle file"""
        with open(path, "rb+") as f:
            data = json.loads(f.read())
        
        time_data = {}
        for i in range(12):  # Q1-Q12
            query_key = f"Q{i+1}"
            time_data[query_key] = {}
            
            id = 0
            for dtype in ["RPQ", "D1", "D2", "D3", "D4", "D5"]:
                if id == 0:  # Skip RPQ
                    id += 1
                    values = list(map(lambda x: x, data[i*6 + id][2]))
                    time_data[query_key][dtype] = values
                else:
                    id += 1
        
        return time_data