"""
Purpose
=======
    Verify the status of datanode(dead or live) from namenode using hdfs dfsadmin -report command

"""
from potluck.nodes import get_nodes_by_type, find_master, connect
from potluck.logging import logger
from potluck.reporting import report

import re
import sys

namenode_alias_list = get_nodes_by_type("NAMENODE")
if (not namenode_alias_list):
    report.fail("No Namenodes in the testbed ")
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
master_node.setMode("shell")

logger.info("Checking dfs report from shell")
output = master_node.run_cmd("sudo -u hdfs hdfs dfsadmin -report")

if re.search("Dead", output, flags=re.I):
   report.fail("One or more datanode is dead.Please check hdfs.")
else:
   logger.info("All Datanodes are live")
