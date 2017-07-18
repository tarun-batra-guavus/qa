"""
Purpose
=======
    Check that pgha_watchdog process is running on all namenodes

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
    logger.info("Checking that pgha-watchdog process is running")
    node = connect(node_alias)
    flag=node.grepProcess(node_alias,"pgha-watchdog")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("watchdog is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("pgha_watchdog process is running on all nodes")
else:
        report.fail("pgha_watchdog process is not running on nodes: %s" %report_str)


