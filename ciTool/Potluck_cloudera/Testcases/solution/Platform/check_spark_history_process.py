"""
Purpose
=======
    Check that Spark-History-Server process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Spark-History-Server process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

sparkhistorynodes = get_nodes_by_type("SPARK-HISTORY")
if (not sparkhistorynodes):
    report.fail("No Spark-History-Server node in the testbed ")

for node_alias in sparkhistorynodes:
    logger.info("Checking that Spark-History-Server process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"HistoryServer")
    if flag ==1:
        logger.info("Spark-History-Server process is running")
    else:
      	report.fail("Spark-History-Server process is not running on node %s" %node_alias)
