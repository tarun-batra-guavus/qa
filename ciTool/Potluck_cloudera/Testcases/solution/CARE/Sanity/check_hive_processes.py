"""
Purpose
=======
    Check that hive process is running on all hive machines

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

hivenodes = get_nodes_by_type("HIVE")
print "hivenodes nodes are" , hivenodes
if (not hivenodes):
    report.fail("No HIVE nodes in the testbed ")
result_dict = {}
report_str = ""
for node_alias in hivenodes:
    logger.info("Checking that HIVE process is running")
    node = connect(node_alias)
    flag = node.checkserviceProcess("hive-metastore")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Hive is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Hive  process is running on all nodes")
else:
        report.fail("Hive process is not running on nodes: %s" %report_str)
