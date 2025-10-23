import http.client
import random
import socket
import subprocess
import sys
import time
import psutil
import shutil, os, glob
from pathlib import Path
from subprocess import Popen
import csv

from .option import (
    CREATE_DB_EXECUTABLE,
    DBS_DIR,
    HOST,
    PORT,
    SERVER_EXECUTABLE,
    SLEEP_DELAY,
    TIMEOUT,
    ROOT_TEST_DIR,
    CWD
)


def create_db(qm_file: Path):
    if not qm_file.is_file():
        sys.exit(1)
    db_dir = DBS_DIR / qm_file.with_suffix("")
    cmd: list[str] = [str(CREATE_DB_EXECUTABLE), str(qm_file), str(db_dir)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return db_dir

def get_mdb_server_memory():
    """
    Returns the memory usage (in MB) of the 'mdb-server' process.
    Returns None if not found.
    """
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            if proc.info['name'] == "mdb-server":
                return proc.info['memory_info'].rss / (1024 * 1024)  # MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def send_query(test: str) -> str | int:
    conn = http.client.HTTPConnection(f"{HOST}:{PORT}")
    conn.request("POST", "/", headers={"Accept": "text/csv"}, body=test)
    response = conn.getresponse()
    if response.getcode() != 200:
        return 1
    return response.read().decode("utf-8")


def start_server(db_dir: Path, timeout=TIMEOUT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (HOST, PORT)

    # Check if port is already in use
    if sock.connect_ex(address) == 0:
        raise SystemError("Port is used")
        sys.exit(1)
    cmd: list[str] = [
        str(SERVER_EXECUTABLE),
        str(db_dir),
        "--timeout",
        str(timeout),
        "--port",
        str(PORT),
    ]
    server_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait for server initialization
    while sock.connect_ex(address) != 0:
        time.sleep(SLEEP_DELAY)
    return server_process


def kill_server(server_process: Popen[bytes]):
    server_process.kill()
    server_process.wait()


def execute_query(server: Popen[bytes] | None, query_str: str) -> str | None:

    conn = http.client.HTTPConnection(f"{HOST}:{PORT}")

    conn.request("POST", "/", headers={"Accept": "text/csv"}, body=query_str)

    response = conn.getresponse()

    if response.getcode() != 200:
        return None

    if server and server.poll() is not None:

        raise SystemError("Server  Crash")

    return response.read().decode("utf-8")


def sample(bound: int, max_size: int):  # type: ignore
    res = []
    random.seed(time.time())
    for _ in range(bound):
        res.append(random.randint(0, max_size))  # type: ignore
    return res  # type: ignore


import shutil
import os

def move_file(source_path, destination_path, create_dirs=False):
    """
    Move a file from source_path to destination_path with enhanced error handling.
    
    Args:
        source_path (str): Path to the source file
        destination_path (str): Path to the destination file or directory
        create_dirs (bool): If True, create destination directories if they don't exist
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if source file exists
        if not os.path.exists(source_path):
            print(f"Error: Source file '{source_path}' does not exist")
            return False
        
        # Check if source is a file (not a directory)
        if not os.path.isfile(source_path):
            print(f"Error: '{source_path}' is not a file")
            return False
        
        # If destination is a directory, use the original filename
        if os.path.isdir(destination_path):
            filename = os.path.basename(source_path)
            destination_path = os.path.join(destination_path, filename)
        
        # Create destination directory if needed
        if create_dirs:
            dest_dir = os.path.dirname(destination_path)
            os.makedirs(dest_dir, exist_ok=True)
        
        # Move the file
        shutil.move(source_path, destination_path)
        print(f"File moved successfully from '{source_path}' to '{destination_path}'")
        return True
        
    except PermissionError:
        print(f"Error: Permission denied when moving '{source_path}'")
        return False
    except shutil.Error as e:
        print(f"Error moving file: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False 


def move_all_json_files(source_dir, destination_dir):
    """
    Move all JSON files from source directory to destination directory.
    
    Args:
        source_dir (str): Source directory containing JSON files
        destination_dir (str): Destination directory
    """
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)
        
        # Find all JSON files in source directory
        json_files = glob.glob(os.path.join(source_dir, "*.json"))
        
        if not json_files:
            print(f"No JSON files found in {source_dir}")
            return False
        
        moved_count = 0
        for json_file in json_files:
            filename = os.path.basename(json_file)
            destination_path = os.path.join(destination_dir, filename)
            
            shutil.move(json_file, destination_path)
            print(f"Moved: {filename}")
            moved_count += 1
        
        print(f"Successfully moved {moved_count} JSON files")
        return True
        
    except Exception as e:
        print(f"Error moving JSON files: {e}")
        return False


def file_handler(name:str):
    log_path = CWD/"z3_debug.log"
    test_dir = ROOT_TEST_DIR / "result" 
    dst_path = ROOT_TEST_DIR / "case-study"/ name
    move_file(log_path, dst_path/"z3_debug.log", create_dirs=True)
    move_all_json_files(test_dir, dst_path)

def clear_directory_recreate(directory_path):
    """
    Clear directory by removing and recreating it.
    This approach completely wipes the directory and recreates it.
    
    Args:
        directory_path (str): Path to the directory to clear
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(directory_path):
            print(f"Directory '{directory_path}' does not exist")
            return False
        
        if not os.path.isdir(directory_path):
            print(f"Error: '{directory_path}' is not a directory")
            return False
        
        # Remove the entire directory
        shutil.rmtree(directory_path)
        
        # Recreate the directory
        os.makedirs(directory_path)
        
        print(f"Successfully cleared and recreated '{directory_path}'")
        return True
        
    except Exception as e:
        print(f"Error clearing directory: {e}")
        return False
    
def prepare():
    remove_dir = ROOT_TEST_DIR / "case-study"
    clear_directory_recreate(remove_dir)

def write_csv(path, data):
    with open(path, "w") as f:
        csv_writer = csv.writer(f)
        for mytuple in data:
            csv_writer.writerow(mytuple)