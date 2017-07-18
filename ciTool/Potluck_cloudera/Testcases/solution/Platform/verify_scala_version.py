"""
Purpose
=======
    Check that Scala version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Scala version on all Scala machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["SCALA"]

scalanodes = get_nodes_by_type("SCALA")

if (not scalanodes):
    report.fail("No Scala nodes in the testbed ")

for node_alias in scalanodes:
    logger.info("Checking that Scala version on all scala machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Scala",version)
    if flag ==1:
        logger.info("Scala version on all scala nodes are as User Specified")
    else:
        report.fail("Scala version on all scala machines are not as User Specified")

