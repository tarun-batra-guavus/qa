"""
Purpose
=======
    Check that Yarn version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Yarn version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["HADOOP-YARN"]

yarnnodes = get_nodes_by_type("HADOOP-YARN")

if (not yarnnodes):
    report.fail("No Yarn nodes in the testbed ")

for node_alias in yarnnodes:
    logger.info("Checking that Yarn version on all Yarn machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("hadoop-yarn",version)
    if flag ==1:
        logger.info("Yarn version on all Yarn nodes are as User Specified")
    else:
        report.fail("Yarn version on all Yarn machines are not as User Specified")

