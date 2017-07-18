"""
Purpose
=======
    Check that Hadoop-Hdfs process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Hadoop-Hdfs process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

hdfsnodes = get_nodes_by_type("HADOOP-HDFS")
if (not hdfsnodes):
    report.fail("No Hadoop-Hdfs node in the testbed ")

for node_alias in hdfsnodes:
    logger.info("Checking that Hadoop-Hdfs process is running")
    node = connect(node_alias)
    flag = node.systemctlProcess("HADOOP-HDFS")
    if flag ==1:
        logger.info("Hadoop-Hdfs process is running on %s node"%node_alias)
    else:
      	report.fail("Hadoop-Hdfs process is not running on node %s" %node_alias)
