"""
Purpose
=======
    Check that Azkaban version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Azkaban version on all Azkaban machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["AZKABAN"]

azkabannodes = get_nodes_by_type("AZKABAN")

if (not azkabannodes):
    report.fail("No Azkaban nodes in the testbed ")

for node_alias in azkabannodes:
    logger.info("Checking that Azkaban version on all machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Azkaban",version)
    if flag ==1:
        logger.info("Azkaban version on all Azkaban nodes are as User Specified")
    else:
        report.fail("Azkaban version on all Azkaban machines are not as User Specified")

