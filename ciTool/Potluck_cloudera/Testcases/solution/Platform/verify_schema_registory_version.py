"""
Purpose
=======
    Check that schema-registry version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that schema-registry version on all schema-registry machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["SCHEMA-REGISTRY"]

schema_registrynodes = get_nodes_by_type("SCHEMA-REGISTRY")

if (not schema_registrynodes):
    report.fail("No schema-registry nodes in the testbed ")

for node_alias in schema_registrynodes:
    logger.info("Checking that schema-registry version on all schema-registry machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("schema-registry",version)
    if flag ==1:
        logger.info("schema-registry version on all schema-registry nodes are as User Specified")
    else:
        report.fail("schema-registry version on all schema-registry machines are not as User Specified")

