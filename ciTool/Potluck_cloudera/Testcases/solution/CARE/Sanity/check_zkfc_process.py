"""
Purpose
=======
    Check that zkfc process is running on all namenodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
namenodes = get_nodes_by_type("NAMENODE")
print "namenodes are" , namenodes
if (not namenodes):
    report.fail("No namenodes in the testbed ")

result_dict = {}
report_str = ""
for node_alias in namenodes:
    logger.info("Checking that zkfc process is running")
    node = connect(node_alias)
    flag=node.grepProcess(node_alias,"DFSZKFailoverController")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("ZKFC is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("ZKFC process is running on all nodes")
else:
        report.fail("ZKFC process is not running on nodes: %s" %report_str)

