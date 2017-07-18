"""
Purpose
=======
    Check that Spark process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that spark process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

sparknodes = get_nodes_by_type("SPARK")
if (not sparknodes):
    report.fail("No Spark node in the testbed ")

for node_alias in sparknodes:
    logger.info("Checking that Spark process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"Spark")
    if flag ==1:
        logger.info("Spark process is running")
    else:
      	report.fail("Spark process is not running on node %s" %node_alias)
