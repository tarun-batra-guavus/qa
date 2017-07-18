"""
Purpose
=======
    Check that Impala process is running on all nodes (namenode/datanode)

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import sys
namenodes = get_nodes_by_type("NAMENODE")
datanodes = get_nodes_by_type("DATANODE")
if (not namenodes) and (not datanodes):
    report.fail("No impala nodes in the testbed ")

result_dict = {}
report_str = ""
for node_alias in namenodes:
    logger.info("Checking that Impala process is running")
    node = connect(node_alias)
    flag_1 = node.grepProcess(node_alias,"impala/sbin/catalogd")
    flag_2 = node.grepProcess(node_alias,"impala/sbin/statestored")
    if flag_1 and flag_2:
	    result_dict[node_alias] = 1
    else:
	    result_dict[node_alias] = 0

for node_alias in datanodes:
    logger.info("Checking that Impala process is running")
    node = connect(node_alias)
    flag_1 = node.grepProcess(node_alias,"impala")
    result_dict[node_alias] = flag_1
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Impala process is running on node %s" %key)
        elif report_str == "":
                report_str = key
	else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Impala  process is running on all nodes")
else:
        report.fail("Impala process is not running on nodes: %s" %report_str)

