"""
Purpose
=======
    Check that PSQL version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that PSQL version on all Ansible machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["POSTGRESQL"]

psqlnodes = get_nodes_by_type("POSTGRESQL")

if (not psqlnodes):
    report.fail("No PSQL nodes in the testbed ")

for node_alias in psqlnodes:
    logger.info("Checking that PSQL version on all PSQL machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersionbyCommand("POSTGRESQL", "psql -V",version)
    if flag ==1:
        logger.info("PSQL version on %s Node nodes are as User Specified"%node_alias)
    else:
        report.fail("PSQL version on %s Node are not as User Specified"%node_alias)

