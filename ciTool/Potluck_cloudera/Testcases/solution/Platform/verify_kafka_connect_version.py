"""
Purpose
=======
    Check that Kafka-Connect version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Kafka-Connect version on all Kafka-Connect machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["KAFKA-CONNECT"]

kafka_connectnodes = get_nodes_by_type("KAFKA-CONNECT")

if (not kafka_connectnodes):
    report.fail("No Kafka-Connect nodes in the testbed ")

for node_alias in kafka_connectnodes:
    logger.info("Checking that Kafka-Connect version on all Avro machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Kafka-Connect",version)
    if flag ==1:
        logger.info("Kafka-Connect version on all Avro nodes are as User Specified")
    else:
        report.fail("Kafka-Connect version on all Avro machines are not as User Specified")

