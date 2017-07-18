"""
Purpose
=======
    Check that Sentry process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Sentry process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

sentrynodes = get_nodes_by_type("SENTRY")
if (not sentrynodes):
    report.fail("No Sentry node in the testbed ")

for node_alias in sentrynodes:
    logger.info("Checking that Sentry process is running")
    node = connect(node_alias)
    flag = node.systemctlProcess("sentry")
    if flag ==1:
        logger.info("Sentry process is running")
    else:
      	report.fail("Sentry process is not running on node %s" %node_alias)
