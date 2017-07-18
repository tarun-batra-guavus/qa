"""
Purpose
=======
    Check that Flannel process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Flannel process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

flannelnodes = get_nodes_by_type("DOCKER1")
if (not flannelnodes):
    report.fail("No Flannel node in the testbed ")

for node_alias in flannelnodes:
    logger.info("Checking that Flannel process is running")
    node = connect(node_alias)
    flag = node.dockerProcess("FLANNEL")
    if flag ==1:
        logger.info("Flannel process is running")
    else:
      	report.fail("Flannel process is not running on node %s" %node_alias)
