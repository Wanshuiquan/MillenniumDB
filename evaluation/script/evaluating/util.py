import http.client
import random
import socket
import subprocess
import sys
import time
from pathlib import Path
from subprocess import Popen

from .option import (
    CREATE_DB_EXECUTABLE,
    DBS_DIR,
    HOST,
    PORT,
    SERVER_EXECUTABLE,
    SLEEP_DELAY,
    TIMEOUT,
)


def create_db(qm_file: Path):
    if not qm_file.is_file():
        sys.exit(1)
    db_dir = DBS_DIR / qm_file.with_suffix("")
    cmd: list[str] = [str(CREATE_DB_EXECUTABLE), str(qm_file), str(db_dir)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return db_dir


def send_query(test: str) -> str | int:
    conn = http.client.HTTPConnection(f"{HOST}:{PORT}")
    conn.request("POST", "/", headers={"Accept": "text/csv"}, body=test)
    response = conn.getresponse()
    if response.getcode() != 200:
        return 1
    return response.read().decode("utf-8")


def start_server(db_dir: Path):
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
        str(TIMEOUT),
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
