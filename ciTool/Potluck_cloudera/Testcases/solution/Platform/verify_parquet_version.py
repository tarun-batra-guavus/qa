"""
Purpose
=======
    Check that Apache Parquet version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Apache Parquet version on all Apache Parquet machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["PARQUET"]

parquetnodes = get_nodes_by_type("PARQUET")

if (not parquetnodes):
    report.fail("No Apache Parquet nodes in the testbed ")

for node_alias in parquetnodes:
    logger.info("Checking that Apache Parquet version on all Apache Parquet machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("Parquet",version)
    if flag ==1:
        logger.info("Apache Parquet version on all Apache Parquet nodes are as User Specified")
    else:
        report.fail("Apache Parquet version on all Apache Parquet machines are not as User Specified")

