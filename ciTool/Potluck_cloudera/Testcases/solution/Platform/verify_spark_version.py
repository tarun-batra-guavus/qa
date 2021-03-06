"""
Purpose
=======
    Check that Spark version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that version on all Spark machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["SPARK"]

sparknodes = get_nodes_by_type("SPARK")

if (not sparknodes):
    report.fail("No Spark nodes in the testbed ")

for node_alias in sparknodes:
    logger.info("Checking that Spark version on all Spark machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("spark",version)
    if flag ==1:
        logger.info("Spark version on all Spark nodes are as User Specified")
    else:
        report.fail("Spark version on all Spark machines are not as User Specified")

