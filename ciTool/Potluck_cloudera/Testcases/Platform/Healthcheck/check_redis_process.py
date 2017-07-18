"""
Purpose
=======
    Check that redis process is running on all redis nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import sys
list = []
redis_nodes = get_nodes_by_type("REDIS")
if (not redis_nodes):
    report.fail("No REDIS Servers in the testbed ")
logger.info("Checking that Redis server process is running")
node = connect(redis_nodes[0])
output = node.run_cmd("/opt/redis/src/redis-cli cluster nodes")
list = output.replace('\r', '').split("\n")
disconnected_list = []
for line in list:
                if "disconnected" in line:
			line = line.split(' ')
			ipport = line[1]
			process = line[2]
			disconnected_list.append(ipport)
			disconnected_list.append(":")
			disconnected_list.append(process)

if len(disconnected_list) == 0:
	logger.info("No disconnected redis process found on nodes")
	logger.info("Redis process is running on all nodes")
else:
	report.fail("Redis process is not running on %s" %disconnected_list)
