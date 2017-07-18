##########
# FILE: settings
#
# PURPOSE
# -------
# All the Framework-Wide will be stored here
# 
# AUTHOR
# ------
# Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>
#
# MODIFICATION HISTORY
# --------------------
# 01-Feb-2013 - sandep.nanda - Initial Creation
#
##########
import os
import sys
from datetime import datetime

now = datetime.now
# Note down the start time
start_time = now()

# Various timestamps needed further in the harness
start_timestamp = start_time.strftime("%Y%m%d%H%M%S")
start_date_str = start_time.strftime("%Y-%m-%d")
start_time_str = start_time.strftime("%H:%M:%S")

time = str(start_date_str) + "_" + str(start_time_str)

# Various Paths required by the framework
SRC_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
SUITES_DIR = os.path.join(ROOT_DIR, "Testsuites")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "Testcases")
TESTBEDS_DIR = os.path.join(ROOT_DIR, "Testbeds")
USER_OUTPUT_DIR = os.path.join(ROOT_DIR, "useroutput", str(time)) 
USER_TESTBEDS_DIR = os.path.abspath(os.path.join(ROOT_DIR, "..", "User_Testbeds"))
USER_SUITES_DIR = os.path.abspath(os.path.join(ROOT_DIR, "..", "User_Testsuites"))
MODULES_DIR = os.path.join(SRC_DIR, "modules")
WEB_DIR = os.path.join(SRC_DIR, "web")
WEB_MODULES_DIR = os.path.join(WEB_DIR, "modules")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
REMOTE_DIR = os.path.join(ROOT_DIR, "remote")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
POTLUCK_SERVER_IP = "192.168.104.242"
POTLUCK_SERVER_PORT = 9899
TMP_DIR = os.path.join(ROOT_DIR, "tmp")     # Directory to save temporary data

# Add required paths 
sys.path.append(MODULES_DIR)
sys.path.append(WEB_DIR)
sys.path.append(WEB_MODULES_DIR)
sys.path.append(SCRIPTS_DIR)

# Hack to find machine NIC IP
# MACHINE_IP = "192.168.0.9"
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("192.168.1.1", 80))
MACHINE_IP = s.getsockname()[0]
s.close()
