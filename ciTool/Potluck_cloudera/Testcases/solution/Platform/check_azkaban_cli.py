import commands
import os
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import sys
namenode_alias_list = get_nodes_by_type("NAMENODE")
if (not namenode_alias_list):
    report.fail("No Namenodes in the testbed ")
counter = 1
if len(namenode_alias_list) > 1:
        logger.info("Setup is HA")
        for node_alias in namenode_alias_list:
                node = connect(node_alias)
		flag = node.grepAzkabanCli()
		if flag ==1:
			logger.info("Azkaban CLI is accessible on node: %s" %node_alias)
		elif flag <>1 and counter < len(namenode_alias_list):
			counter = counter + 1
		else:
			report.fail("Azkaban process is not running on node: %s "%node_alias)
		

