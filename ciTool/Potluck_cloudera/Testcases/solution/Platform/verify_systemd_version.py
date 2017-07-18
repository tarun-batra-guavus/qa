"""
Purpose
=======
    Check that Systemd version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Systemd version on all Systemd machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["SYSTEMD"]

systemdnodes = get_nodes_by_type("SYSTEMD")

if (not systemdnodes):
    report.fail("No Systemd nodes in the testbed ")

for node_alias in systemdnodes:
    logger.info("Checking that Systemd version on all Systemd machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Systemd",version)
    if flag ==1:
        logger.info("Systemd version on all Systemd nodes are as User Specified")
    else:
        report.fail("Systemd version on all Systemd machines are not as User Specified")

