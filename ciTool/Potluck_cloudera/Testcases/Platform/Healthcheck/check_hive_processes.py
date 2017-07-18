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

for node_alias in hivenodes:
    logger.info("Checking that HIVE process is running")
    node = connect(node_alias)
    flag = node.checkserviceProcess("hive-metastore")
    if flag ==1:
	logger.info("Hive process is running")
    else:
	report.fail("Hive process is not running on node %s" %node_alias)
