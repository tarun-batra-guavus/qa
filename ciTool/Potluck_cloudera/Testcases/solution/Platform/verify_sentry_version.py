"""
Purpose
=======
    Check that Sentry version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Sentry version on all Sentry machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["SENTRY"]

sentrynodes = get_nodes_by_type("SENTRY")

if (not sentrynodes):
    report.fail("No Sentry nodes in the testbed ")

for node_alias in sentrynodes:
    logger.info("Checking that Sentry version on all Sentry machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("sentry",version)
    if flag ==1:
        logger.info("Sentry version on all Sentry nodes are as User Specified")
    else:
        report.fail("Sentry version on all Sentry machines are not as User Specified")

