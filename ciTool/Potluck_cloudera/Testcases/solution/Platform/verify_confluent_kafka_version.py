"""
Purpose
=======
    Check that Confluent-Kafka version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Confluent-Kafka version on all Confluent-Kafka machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["CONFLUENT-KAFKA"]

confluent_kafkanodes = get_nodes_by_type("CONFLUENT-KAFKA")

if (not confluent_kafkanodes):
    report.fail("No Confluent-Kafka nodes in the testbed ")

for node_alias in confluent_kafkanodes:
    logger.info("Checking that Confluent-Kafka version on all Avro machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Confluent-Kafka",version)
    if flag ==1:
        logger.info("Confluent-Kafka version on all Avro nodes are as User Specified")
    else:
        report.fail("Confluent-Kafka version on all Avro machines are not as User Specified")

