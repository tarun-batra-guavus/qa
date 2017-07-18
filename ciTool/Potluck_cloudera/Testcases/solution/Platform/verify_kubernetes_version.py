"""
Purpose
=======
    Check that Kubernetes version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that  version on all Kubernetes nodes are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["KUBERNETES"]
kubernetesnodes = get_nodes_by_type("KUBERNETES")

if (not kubernetesnodes):
    report.fail("No Kubernetes nodes in the testbed ")

for node_alias in kubernetesnodes:
    logger.info("Checking that Kubernetes version on all Kubernetes nodes are as User Specified")
    node = connect(node_alias)
    flag = node.grepDockerVersions("KUBERNETES",version)
    if flag ==1:
        logger.info("Kubernetes version on all Kubernetes nodes are as User Specified")
    else:
        report.fail("Kubernetes version on all Kubernetes nodes are not as User Specified")

