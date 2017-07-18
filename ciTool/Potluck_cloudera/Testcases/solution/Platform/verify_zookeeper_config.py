"""
Purpose
=======
    Verify that Zookeeper config is same on all zookeeper nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import *
import os
import sys
zookeeper_node_type = "ZOOKEEPER"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
zookeepernodes = get_nodes_by_type("ZOOKEEPER")
if (not zookeepernodes):
    report.fail("No zookeepernodes in the testbed ")
if len(zookeepernodes) == 1:
    report.fail("Only one Zookeeper node available in Testbed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %zookeepernodes)
filelist = []
base_folder = zookeepernodes[0]
diffkeys = []
filelist=obj_parser.createfilelist(configdict,zookeeper_node_type)
print "filelist is :" ,filelist
for filename in filelist:
	for node_alias in zookeepernodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + zookeeper_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)
folder = os.listdir(USER_OUTPUT_DIR + "/" + zookeeper_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + zookeeper_node_type + "/" + folder):
	list_folder = os.listdir(USER_OUTPUT_DIR + "/" + zookeeper_node_type)
	print "calling diff function..."
	for element in obj_parser.diff_func(file,list_folder,zookeeper_node_type,base_folder):
		diffkeys.append(element)

if len(diffkeys) == 0:
        logger.info("No diff found in Zookeeper job configs")
else:
	logger.info("List of parameters in which difference exist is (%s):" %diffkeys)
	difffile = obj_parser.printdiff(diffkeys,"zookeeper_configs")
  	report.fail("Diff found in zookeeper configs among nodes (%s).Please check the difffile (%s)" % (zookeepernodes,difffile))
