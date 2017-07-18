"""
Purpose
=======
    Verify that Azkaban config is same on all azkaban nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import *
import os
import sys
azkaban_node_type = "AZKABAN"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
azkabannodes = get_nodes_by_type("AZKABAN")
diffkeys = []
if (not azkabannodes):
    report.fail("No azkabannodes in the testbed ")
if len(azkabannodes) == 1:
    report.fail("Only one Azkaban node mentioned in Testbed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %azkabannodes)
filelist = []
base_folder = azkabannodes[0]
filelist=obj_parser.createfilelist(configdict,azkaban_node_type)
for filename in filelist:
	for node_alias in azkabannodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + azkaban_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)

### Checking the difference in configs ###

folder = os.listdir(USER_OUTPUT_DIR + "/" + azkaban_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + azkaban_node_type + "/" + folder):
	list_folder = os.listdir(USER_OUTPUT_DIR + "/" + azkaban_node_type)
	for element in obj_parser.diff_func(file,list_folder,azkaban_node_type,base_folder):
                diffkeys.append(element)
logger.info("Difference found in keys list is %s:" %diffkeys)
if len(diffkeys) == 0:
        logger.info("No diff found in Azkaban configs")
#### Printing the final result ###
else:
        logger.info("List of difference parameters is (%s):" %diffkeys)
        difffile = obj_parser.printdiff(diffkeys,"azkaban_configs")
        report.fail("Diff found in azkaban configs among nodes (%s).Please check the difffile (%s)" % (azkabannodes,difffile))


