"""
Purpose
=======
    Check that PUPPET version on its respective Nodes are as User Specified

Test Steps
==========
    1. Goto to shell
    2. Execute "rpm -qa | grep -i "componentName" | grep "version"" and check that Puppet version on all Puppet machines are as User Specified
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
obj_parser = parser()
versiondict ={}

### Creating A dictionary with Structure [Component]:[Version] ###
versiondict = obj_parser.create_dict_version("userinput/version_info_old.txt")
version=versiondict["PUPPET"]

puppetnodes = get_nodes_by_type("PUPPET")

if (not puppetnodes):
    report.fail("No PUPPET nodes in the testbed ")

for node_alias in puppetnodes:
    logger.info("Checking that Puppet version on all Puppet machines are as User Specified")
    node = connect(node_alias)
    flag = node.grepVersion("puppet-agent",version)
    if flag ==1:
        logger.info("PUPPET version on all Puppet nodes are as User Specified")
    else:
        report.fail("PUPPET version on all Puppet machines are not as User Specified")

