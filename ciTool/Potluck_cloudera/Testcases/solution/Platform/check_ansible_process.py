"""
Purpose
=======
    Check that Ansible process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Ansible process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

ansiblenode = get_nodes_by_type("ANSIBLE")
if (not ansiblenode):
    report.fail("No ANSIBLE node in the testbed ")

for node_alias in ansiblenode:
    logger.info("Checking that Ansible process is running")
    node = connect(node_alias)
    flag = node.grepProcessNotRunning(node_alias,"ansible")
    if flag ==0:
    	logger.info("Ansible process is running")
    else:
    	report.fail("Ansible process is not running on node %s" %node_alias)
