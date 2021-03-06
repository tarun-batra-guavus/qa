"""
Purpose
=======
    Check that Avro version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Avro version on all Avro machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["AVRO"]

avronodes = get_nodes_by_type("AVRO")

if (not avronodes):
    report.fail("No Avro nodes in the testbed ")

for node_alias in avronodes:
    logger.info("Checking that Avro version on all Avro machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Avro",version)
    if flag ==1:
        logger.info("Avro version on all Avro nodes are as User Specified")
    else:
        report.fail("Avro version on all Avro machines are not as User Specified")

