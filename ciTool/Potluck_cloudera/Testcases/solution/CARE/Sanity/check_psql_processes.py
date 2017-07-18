"""
Purpose
=======
    Check that PSQL process is running on all psql machines

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import sys
psqlnodes = get_nodes_by_type("PGSQL")
print "psqlnodes nodes are" , psqlnodes
if (not psqlnodes):
    report.fail("No pgsql nodes in the testbed ")

result_dict = {}
report_str = ""
for node_alias in psqlnodes:
    logger.info("Checking that pgsql process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"/usr/pgsql-9.4/bin/postgres")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Pgsql is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Pgsql process is running on all nodes")
else:
        report.fail("Pgsql process is not running on node: %s" %report_str)



