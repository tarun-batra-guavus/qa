"""
Purpose
=======
    Check that Hyperkube process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Hyperkube & Kubernetes process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
kubernetenodes = get_nodes_by_type("KUBERNETES")
hyperkubenodes = get_nodes_by_type("DOCKER1")
if (not hyperkubenodes):
    report.fail("No Hyperkube node in the testbed ")
if (not kubernetenodes):
    report.fail("No Kubernets node in the testbed ")

for node_alias in hyperkubenodes:
    logger.info("Checking that Hyperkube Proxy process is running")
    node = connect(node_alias)
    flag = node.dockerProcess("hyperkube proxy")
    if flag ==1:
        logger.info("Hyperkube Proxy process is running")
    else:
      	report.fail("Hyperkube Proxy process is not running on node %s" %node_alias)


for node_alias in kubernetenodes:
    logger.info("Checking that Kubernetes process is running")
    node = connect(node_alias)
    flag_1 = node.dockerProcess("hyperkube controlle")
    flag_2 = node.dockerProcess("hyperkube scheduler")
    flag_3 = node.dockerProcess("hyperkube apiserver")
    flag_4 = node.dockerProcess("hyperkube proxy")
    if flag_1 ==1 & flag_2 ==1 & flag_3 ==1 & flag_4 ==1:
        logger.info("Kubernetes process is running")
    else:
        report.fail("Kubernetes process is not running on node %s" %node_alias)
