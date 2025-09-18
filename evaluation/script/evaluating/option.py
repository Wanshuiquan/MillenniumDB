
from pathlib import Path
# some options
YOUTUBE_SIZE =  1134891

FB_SIZE = 4000

POKEC_SIZE = 1632803

# Host and port the server will listen on
HOST = "127.0.0.1"
PORT = 8080

# Time between checks for server initialization
SLEEP_DELAY = 0.01

# Maximum time in seconds that the server will wait for a query
TIMEOUT = 30

# Assume that the script is run from the root directory
CWD = Path().cwd()
ROOT_TEST_DIR = CWD / "evaluation"
DATA_DIR = ROOT_TEST_DIR / "data"
DBS_DIR = ROOT_TEST_DIR / "database"
SERVER_LOGS_DIR = ROOT_TEST_DIR / "tmp/server-logs"

# Executables
CREATE_DB_EXECUTABLE = CWD / "build/Release/bin/mdb-import"
SERVER_EXECUTABLE = CWD / "build/Release/bin/mdb-server"

# Width of each column of test outputs
OUTPUT_COLUMN_WIDTH = 50

LOGGING_LEVELS = {
    "SUMMARY": True,
    "ERROR": True,
    "WARNING": True,
    "OUTPUT": True,
    "CORRECT": False,
    "BEGIN": False,
    "END": False,
    "SKIPPED": False,
    "DEBUG": False,
    "SERVER_LOG": False,
}


def QUERY_EXECUTABLE():
    return None
