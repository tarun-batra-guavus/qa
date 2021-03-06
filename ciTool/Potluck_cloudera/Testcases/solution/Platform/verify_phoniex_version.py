"""
Purpose
=======
    Check that Phoenix version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Phoenix version on all Phoenix machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["PHOENIX"]

phoenixnodes = get_nodes_by_type("PHOENIX")

if (not phoenixnodes):
    report.fail("No Phoenix nodes in the testbed ")

for node_alias in phoenixnodes:
    logger.info("Checking that Phoenix version on all Phoenix machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Phoenix",version)
    if flag ==1:
        logger.info("Phoenix version on all Phoenix nodes are as User Specified")
    else:
        report.fail("Phoenix version on all Phoenix machines are not as User Specified")

