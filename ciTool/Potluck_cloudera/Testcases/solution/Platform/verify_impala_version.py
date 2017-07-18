"""
Purpose
=======
    Check that Impala version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Impala version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["IMPALA"]

impalanodes = get_nodes_by_type("IMPALA")

if (not impalanodes):
    report.fail("No Impala nodes in the testbed ")

for node_alias in impalanodes:
    logger.info("Checking that Impala version on all Impala machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("impala-shell",version)
    if flag ==1:
        logger.info("Impala version on all Impala nodes are as User Specified")
    else:
        report.fail("Impala version on all Impala machines are not as User Specified")

