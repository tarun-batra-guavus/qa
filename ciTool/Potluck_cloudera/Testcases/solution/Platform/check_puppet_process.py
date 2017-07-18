"""
Purpose
=======
    Check that Puppet process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Puppet process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

puppetnodes = get_nodes_by_type("PUPPET")
if (not puppetnodes):
    report.fail("No Puppet node in the testbed ")

for node_alias in puppetnodes:
    logger.info("Checking that Puppet process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"puppet-server")
    if flag ==1:
        logger.info("Puppet process is running")
    else:
      	report.fail("Puppet process is not running on node %s" %node_alias)
