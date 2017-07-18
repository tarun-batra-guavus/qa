"""
Purpose
=======
    Check that Docker version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that version on all Docker nodes are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["DOCKER"]

dockernodes = get_nodes_by_type("DOCKER")

if (not dockernodes):
    report.fail("No Docker nodes in the testbed ")

for node_alias in dockernodes:
    logger.info("Checking that Docker version on all Docker nodes are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Docker",version)
    if flag ==1:
        logger.info("Docker version on all Docker nodes are as User Specified")
    else:
        report.fail("Docker version on all Docker nodes are not as User Specified")

