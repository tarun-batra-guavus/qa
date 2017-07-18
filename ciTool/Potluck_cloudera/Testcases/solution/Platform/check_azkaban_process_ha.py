from time import sleep
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import os
import sys
namenode_alias_list = get_nodes_by_type("NAMENODE")
azkaban_ha_nodes = namenode_alias_list
if (not namenode_alias_list):
    report.fail("No Namenodes in the testbed ")
counter = 1
if len(namenode_alias_list) > 1:
        logger.info("Setup is HA")
	for node_alias in namenode_alias_list:
		node = connect(node_alias)
		node.setMode("shell")
		#flag = "flag" + "_" + node_alias
		flag = node.grepProcess(node_alias,"azkabansingleserver")
		if flag ==1:
			logger.info("Before HA, Azkaban process is running on node: %s" %node_alias)
			node.reboot()
			azkaban_ha_nodes.remove(node_alias)
			print "#################"
			print "azkaban_ha_nodes:%s"%azkaban_ha_nodes
			sleep(120)
			for nodes_ha in azkaban_ha_nodes:
				node = connect(nodes_ha)
				print "#################"
				print "Running following Command"
				print "node = connect(%s)"%nodes_ha
				os.system("ifconfig")
				flag = node.grepProcess(node_alias,"azkabansingleserver")
				if flag ==1:
                        		logger.info("After HA, Azkaban process is running on node: %s" %nodes_ha)
				elise:
					report.fail("After HA, Azkaban process is not running on node: %s "%nodes_ha)
		elif flag <>1 and counter < len(namenode_alias_list):
			counter = counter + 1
		else:
			report.fail("Azkaban process is not running on node: %s "%node_alias)
		

