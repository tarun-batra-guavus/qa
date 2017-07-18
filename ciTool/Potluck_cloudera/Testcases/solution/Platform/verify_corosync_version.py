"""
Purpose
=======
    Check that Corosync version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Corosync version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["COROSYNC"]

corosyncnodes = get_nodes_by_type("COROSYNC")

if (not corosyncnodes):
    report.fail("No Corosync nodes in the testbed ")

for node_alias in corosyncnodes:
    logger.info("Checking that Corosync version on all Corosync machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersionbyCommand("Corosync", "corosync -v",version)
    if flag ==1:
        logger.info("Corosync version on %s Node nodes are as User Specified"%node_alias)
    else:
        report.fail("Corosync version on %s Node are not as User Specified"%node_alias)

