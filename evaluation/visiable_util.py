import pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import os 
import re
Z3_LOG_PATHS = {
        "L1": "case-study/ldbc10/z3_debug.log",
        "L0": "case-study/ldbc01/z3_debug.log", 
        "PO": "case-study/pokec/z3_debug.log",
        "TE": "case-study/telecom/z3_debug.log",
        "IL": "case-study/icij-leak/z3_debug.log",
        "IP": "case-study/paradise/z3_debug.log"
    }

OPTIMIZED_PATHS = {"L1":"case-study/ldbc01/ldbc01_statistic.pkl", 
         "L0":"case-study/ldbc01/ldbc01_statistic.pkl", 
         "PO":"case-study/pokec/pokec_statistic.pkl",
         "TE":"case-study/telecom/telecom_statistic.pkl",
         "IL":"case-study/icij-leak/icij_leak_statistic.pkl",
         "IP":"case-study/paradise/icij_paradise_statistic.pkl"}

DATASET_STAT ={
            "L1": (29987850,  178101408),
        "L0": (184344, 767828), 
        "PO": (1632806,30622564),
        "TE": (170000, 50000000),
        "IL": (1908480,  3193390),
        "IP": (163420, 364456)
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
        data = pickle.loads(f.read())
    
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
        data = pickle.loads(f.read())
    
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
            data = pickle.loads(f.read())
        
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
