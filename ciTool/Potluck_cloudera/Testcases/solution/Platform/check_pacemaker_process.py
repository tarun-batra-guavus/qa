"""
Purpose
=======
    Check that pacemaker/pacemaker process is running on all pacemakerh nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
pacemakernodes = get_nodes_by_type("PACEMAKER")
if (not pacemakernodes):
    report.fail("No pacemaker nodes in the testbed ")
result_dict = {}
report_str = ""
for node_alias in pacemakernodes:
    logger.info("Checking that pacemaker process is running")
    node = connect(node_alias)
    flag=node.grepProcess(node_alias,"pacemaker")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Pacemaker is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Pacemaker  process is running on all nodes")
else:
        report.fail("Pacemaker process is not running on nodes: %s" %report_str)

