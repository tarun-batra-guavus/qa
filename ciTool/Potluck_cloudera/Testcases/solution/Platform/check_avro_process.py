"""
Purpose
=======
    Check that avro process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Apache Avro process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

avronodes = get_nodes_by_type("AVRO")
if (not avronodes):
    report.fail("No AVRO node in the testbed ")

for node_alias in avronodes:
    logger.info("Checking that AVRO process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"avro")
    if flag ==1:
        logger.info("Avro process is running")
    else:
      	report.fail("Avro process is not running on node %s" %node_alias)
