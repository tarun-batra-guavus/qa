"""
Purpose
=======
    Check that Phoenix process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Phoenix process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

phoenixnodes = get_nodes_by_type("PHOENIX")
if (not phoenixnodes):
    report.fail("No PHOENIX node in the testbed ")

for node_alias in phoenixnodes:
    logger.info("Checking that Phoenix process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"Phoenix")
    if flag ==1:
    	logger.info("Phoenix process is running")
    else:
    	report.fail("Phoenix process is not running on node %s" %node_alias)
