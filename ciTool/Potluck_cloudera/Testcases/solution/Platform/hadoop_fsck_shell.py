"""
Purpose
=======
    Check the status of hdfs using hdfs hadoop fsck / command

"""
from potluck.nodes import get_nodes_by_type, connect
from potluck.logging import logger
from potluck.reporting import report

import re
namenode_alias_list = get_nodes_by_type("NAMENODE")

# Find which node is TM Master
if len(namenode_alias_list) > 1:
        logger.info("Setup is HA")
        for node_alias in namenode_alias_list:
                node = connect(node_alias)
                print "node connected is :",node_alias
                role = node.getClusterRole()
                if role == 'master':
                        master_namenode = node_alias
                        logger.info("master namenode is %s" %master_namenode)
                        break
else:
        logger.info("Setup is Standalone")
        node_alias = namenode_alias_list[0]
        master_namenode = node_alias
master_node = connect(master_namenode)

# Go to shell mode
master_node.setMode("shell")

logger.info("Running hadoop fsck from shell")
output = master_node.run_cmd("sudo -u hdfs hadoop fsck /")

if re.search("Status:\s*HEALTHY", output, flags=re.I):
   logger.info("HDFS status is healthy")
else:
   report.fail("HDFS status is unhealthy")
