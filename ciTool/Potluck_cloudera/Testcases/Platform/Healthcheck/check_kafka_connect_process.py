"""
Purpose
=======
    Verify that Kafka connect process is running on all kafka-connect nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

kafkanodes = get_nodes_by_type("KAFKA-CONNECT")
if (not kafkanodes):
    report.fail("No kafkanodes in the testbed ")

for node_alias in kafkanodes:
    logger.info("Checking that kafka connect process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"ConnectStandalone")
    if flag == 1:
        logger.info("Kafka connect process is running on node %s" %node_alias)
    else:
      	report.fail("Kafka connect process is not running on node %s" %node_alias)
