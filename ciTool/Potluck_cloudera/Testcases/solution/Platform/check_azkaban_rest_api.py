import os.path
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
		node.setMode("shell")
		fileExist_status = node.fileExist("/opt/azkaban/solo-server/conf/azkaban.properties")
		if fileExist_status == 1:
			output = node.sendCmd("cat /opt/azkaban/solo-server/conf/azkaban.properties | grep -i \"jetty.port\"")
			port_line = output.split("\n")
			port = port_line[1].split("=")
			flag = node.azkabanRestAPI(node_alias,port)
			if flag ==1:
				logger.info("Azkaban REST API is accessible on node: %s" %node_alias)
				counter = counter + 1
			else:
				report.fail("Azkaban Process is not running on node: %s "%node_alias)
		else:
			logger.info("Azkaban process is not running on node: %s "%node_alias)
		

