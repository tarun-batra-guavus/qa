"""
Purpose
=======
    Check that Hbase version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that hive version on all hive machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["HBASE"]

hbasenodes = get_nodes_by_type("HBASE")

if (not hbasenodes):
    report.fail("No Hbase nodes in the testbed ")

for node_alias in hbasenodes:
    logger.info("Checking that Hbase version on all hive machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"hbase-master")
    if flag ==1:
        logger.info("Hbase version on all hive nodes are as User Specified")
    else:
        report.fail("Hbase version on all hive machines are not as User Specified")

