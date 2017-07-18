"""
Purpose
=======
    Check that Hyperkube version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that  version on all  nodes are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["HYPERKUBE"]
hyperkubenodes = get_nodes_by_type("DOCKER1")

if (not hyperkubenodes):
    report.fail("No Hyperkube nodes in the testbed ")

for node_alias in hyperkubenodes:
    logger.info("Checking that Hyperkube version on all  nodes are as User Specified")
    node = connect(node_alias)
    flag = node.grepDockerVersions("HYPERKUBE",version)
    if flag ==1:
        logger.info("Hyperkube version on all docker nodes are as User Specified")
    else:
        report.fail("Hyperkube version on all docker nodes are not as User Specified")

