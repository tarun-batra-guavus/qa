"""
Purpose
=======
    Check that Etcd process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Etcd process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

etcdnodes = get_nodes_by_type("ETCD")
if (not etcdnodes):
    report.fail("No Docker node in the testbed ")

for node_alias in etcdnodes:
    logger.info("Checking that Etcd process is running")
    node = connect(node_alias)
    flag = node.dockerProcess("ETCD")
    if flag ==1:
        logger.info("Etcd process is running")
    else:
      	report.fail("Etcd process is not running on node %s" %node_alias)
