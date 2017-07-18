"""
Purpose
=======
    Check that all Kafka's brokers are listed in Zookeeper

Test Steps
==========
    1. Goto to shell
    2. Execute "ls /brokers/ids" in zookeeper-shell and checking that all Kafka's brokers are listed in Zookeeper
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

kafkanodes = get_nodes_by_type("CONFLUENT-KAFKA")
if (not kafkanodes):
    report.fail("No Confluent Kafka node in the testbed ")

number_of_nodes = len(kafkanodes)
max_number_of_connectors = 0
if number_of_nodes%2 == 0:
	max_number_of_connectors = (number_of_nodes-1)
else:
	max_number_of_connectors = number_of_nodes

for node_alias in kafkanodes:
    logger.info("Checking that all Kafka's brokers are listed in Confluent Kafka")
    node = connect(node_alias)
    flag = node.kafkaBrokers(node_alias)
    if int(flag) == len(kafkanodes):
        logger.info("all Kafka's brokers are listed in Confluent Kafka")
    else:
      	report.fail("Not all Kafka's brokers are listed on node %s" %node_alias)
