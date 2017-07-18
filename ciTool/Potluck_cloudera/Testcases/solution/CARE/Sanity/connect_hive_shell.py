"""
Purpose
=======
    Check that hive db is connecting and hive shell commands are running fine

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.healthcheck import healthcheck

namenode_alias_list = get_nodes_by_type("HIVE")
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
flag = master_node.connecthivedb()
if flag ==1:
	logger.info("Hive db is connecting")
else:
        report.fail("Hive db is not running on node %s" %node_alias)
