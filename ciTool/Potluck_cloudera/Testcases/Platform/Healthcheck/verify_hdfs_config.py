"""
Purpose
=======
    Check that hdfs config is same on all namenodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import USER_OUTPUT_DIR
import os
import sys
name_node_type = "HDFS"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
namenodes = get_nodes_by_type("NAMENODE")
if (not namenodes):
    report.fail("No namenodes in the testbed ")
if len(namenodes) == 1:
    report.fail("Only one namenode available in TestBed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)..." %namenodes)
filelist = []
base_folder = namenodes[0]
diffkeys = []
filelist=obj_parser.createfilelist(configdict,name_node_type)
logger.info("Config Difference to be taken among nodes (%s) among files(%s)..." %(namenodes,filelist))
for filename in filelist:
	for node_alias in namenodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + name_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)
### Checking the difference in configs ###

folder = os.listdir(USER_OUTPUT_DIR + "/" + name_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + name_node_type + "/" + folder):
	list_folder = os.listdir(USER_OUTPUT_DIR + "/" + name_node_type)
	for element in obj_parser.diff_func_xml(file,list_folder,name_node_type,base_folder):
		diffkeys.append(element)
if len(diffkeys) == 0:
        logger.info("No diff found in Hdfs configs among nodes (%s)" %namenodes)
#### Printing the final result ###
else:
	logger.info("List of difference parameters is %s:" %diffkeys)
        difffile = obj_parser.printdiff(diffkeys,"namenode_configs")
        report.fail("Diff found in namenode configs among nodes (%s).Please check the difffile (%s)" % (namenodes,difffile))
