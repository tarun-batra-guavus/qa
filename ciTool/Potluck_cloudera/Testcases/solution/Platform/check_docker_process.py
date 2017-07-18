"""
Purpose
=======
    Check that avro process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Apache Docker-Engine process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

dockernodes = get_nodes_by_type("DOCKER1")
if (not dockernodes):
    report.fail("No Docker-Engine node in the testbed ")

for node_alias in dockernodes:
    logger.info("Checking that Docker-Engine process is running")
    node = connect(node_alias)
    flag = node.systemctlProcess("docker")
    if flag ==1:
        logger.info("Docker-Engine process is running")
    else:
      	report.fail("Docker-Engine process is not running on node %s" %node_alias)
