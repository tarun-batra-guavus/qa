"""
Purpose
=======
    Check that kafka schema-registry process is running on all KAFKA-SCHEMA nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

kafkanodes = get_nodes_by_type("KAFKA-SCHEMA")
if (not kafkanodes):
    report.fail("No kafkanodes in the testbed ")
result_dict = {}
report_str = ""
for node_alias in kafkanodes:
    logger.info("Checking that kafka process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"schema-registry.properties")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Kafka schema registery process is running on node %s" %key)
        elif report_str == "":
                report_str = key
	else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Kafka schema registery process is running on all nodes")
else:
        report.fail("Kafka schema registery process is not running on nodes: %s" %report_str)

