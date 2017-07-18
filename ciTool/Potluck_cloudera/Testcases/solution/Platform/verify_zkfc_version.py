"""
Purpose
=======
    Check that Zkfc version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Zkfc version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["ZKFC"]

zkfcnodes = get_nodes_by_type("ZKFC")

if (not zkfcnodes):
    report.fail("No Zkfc nodes in the testbed ")

for node_alias in zkfcnodes:
    logger.info("Checking that Zkfc version on all Zkfc machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Zkfc",version)
    if flag ==1:
        logger.info("Zkfc version on all Zkfc nodes are as User Specified")
    else:
        report.fail("Zkfc version on all Zkfc machines are not as User Specified")

