"""
Purpose
=======
    Check that HA proxy process is running on all HA proxy(Loadbalancer) machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -i tomcat | grep -v grep" and check that tomcat process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
lbnodes = get_nodes_by_type("HAPROXY")
print "Load Balancer nodes are" , lbnodes
if (not lbnodes):
    report.fail("No lbnodes in the testbed ")

for node_alias in lbnodes:
    logger.info("Checking that HA Proxy process is running on loadbalancer nodes")
    node = connect(node_alias)
    output_1=node.grepProcess(node_alias,"haproxy")
    if output_1==1 :
        logger.info("HAProxy is running on nodes %s" %lbnodes)
    else:
        report.fail("HAProxy is not running on node %s" %lbnodes)
