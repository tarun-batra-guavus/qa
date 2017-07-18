"""
Purpose
=======
    Check that corosync/pacemaker process is running on all corosynch nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
corosyncnodes = get_nodes_by_type("COROSYNC")
if (not corosyncnodes):
    report.fail("No corosync nodes in the testbed ")
result_dict = {}
report_str = ""
for node_alias in corosyncnodes:
    logger.info("Checking that corosync process is running")
    node = connect(node_alias)
    flag=node.grepProcess(node_alias,"corosync")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Corosync is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Corosync  process is running on all nodes")
else:
        report.fail("Corosync process is not running on nodes: %s" %report_str)

