"""
Purpose
=======
    Check that Spark-History version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that version on all Spark-History machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["SPARK-HISTORY"]

sparkhistorynodes = get_nodes_by_type("SPARK-HISTORY")

if (not sparkhistorynodes):
    report.fail("No Spark-History nodes in the testbed ")

for node_alias in sparkhistorynodes:
    logger.info("Checking that Spark-History version on all Spark-History machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("spark-history-server",version)
    if flag ==1:
        logger.info("Spark-History version on all Spark-History nodes are as User Specified")
    else:
        report.fail("Spark-History version on all Spark-History machines are not as User Specified")

