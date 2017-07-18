"""
Purpose
=======
    Check that Impala process is running on all nodes (namenode/datanode)

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

namenodes = get_nodes_by_type("NAMENODE")
datanodes = get_nodes_by_type("DATANODE")
if (not namenodes) and (not datanodes):
    report.fail("No impala nodes in the testbed ")

for node_alias in namenodes:
    logger.info("Checking that impala process is running on namenodes")
    node = connect(node_alias)
    output_1 = node.grepProcess(node_alias,"impala/sbin/catalogd")
    output_2 = node.grepProcess(node_alias,"impala/sbin/statestored")
    if output_1 ==1 and output_2 ==1:
	logger.info("Impala process is running on namenodes")
    else:
	report.fail("Impala process is not running on namenode %s" %node_alias)
for node_alias in datanodes:
    logger.info("Checking that impala process is running on datanodes")
    node = connect(node_alias)
    output_1 = node.grepProcess(node_alias,"impala")
    if output_1 ==1:
	logger.info("Impala process is running on datanodes")
    else:
	report.fail("Impala process is not running on datanode %s" %node_alias)
