"""
Purpose
=======
    Check that Redis version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Redis version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["REDIS"]

redisnodes = get_nodes_by_type("REDIS")

if (not redisnodes):
    report.fail("No Redis nodes in the testbed ")

for node_alias in redisnodes:
    logger.info("Checking that Redis version on all Redis machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Redis",version)
    if flag ==1:
        logger.info("Redis version on all Redis nodes are as User Specified")
    else:
        report.fail("Redis version on all Redis machines are not as User Specified")

