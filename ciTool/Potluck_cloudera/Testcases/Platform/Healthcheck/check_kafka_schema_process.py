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

for node_alias in kafkanodes:
    logger.info("Checking that kafka process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"schema-registry.properties")
    if flag == 1:
        logger.info("Kafka schema registery process is running on node %s" %node_alias)
    else:
      	report.fail("Kafka schema registery process is not running on node %s" %node_alias)
