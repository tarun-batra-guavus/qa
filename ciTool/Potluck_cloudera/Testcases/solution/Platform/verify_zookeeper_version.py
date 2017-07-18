"""
Purpose
=======
    Check that Zookeeper version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Zookeeper version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["ZOOKEEPER"]

zookeepernodes = get_nodes_by_type("ZOOKEEPER")

if (not zookeepernodes):
    report.fail("No Zookeeper nodes in the testbed ")

for node_alias in zookeepernodes:
    logger.info("Checking that Zookeeper version on all Zookeeper machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Zookeeper",version)
    if flag ==1:
        logger.info("Zookeeper version on all Zookeeper nodes are as User Specified")
    else:
        report.fail("Zookeeper version on all Zookeeper machines are not as User Specified")

