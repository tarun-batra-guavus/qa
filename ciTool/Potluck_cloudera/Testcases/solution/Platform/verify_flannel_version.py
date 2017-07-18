"""
Purpose
=======
    Check that Flannel version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that  version on all Flannel nodes are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["FLANNEL"]
flannelnodes = get_nodes_by_type("FLANNEL")

if (not flannelnodes):
    report.fail("No Flannel nodes in the testbed ")

for node_alias in flannelnodes:
    logger.info("Checking that Flannel version on all Flannel nodes are as User Specified")
    node = connect(node_alias)
    flag = node.grepDockerVersions("FLANNEL",version)
    if flag ==1:
        logger.info("Flannel version on all Flannel nodes are as User Specified")
    else:
        report.fail("Flannel version on all Flannel nodes are not as User Specified")

