"""
Purpose
=======
    Check that Hadoop-Yarn process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Hadoop-Yarn process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

yarnnodes = get_nodes_by_type("HADOOP-YARN")
if (not yarnnodes):
    report.fail("No Hadoop-Yarn node in the testbed ")

for node_alias in yarnnodes:
    logger.info("Checking that Hadoop-Yarn process is running")
    node = connect(node_alias)
    flag = node.systemctlProcess("HADOOP-YARN")
    if flag ==1:
        logger.info("Hadoop-Yarn process is running on %s node"%node_alias)
    else:
      	report.fail("Hadoop-Yarn process is not running on node %s" %node_alias)
