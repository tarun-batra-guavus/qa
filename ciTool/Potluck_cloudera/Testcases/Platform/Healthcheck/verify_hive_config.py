"""
Purpose
=======
    Verify that hive config is same on all hive nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import USER_OUTPUT_DIR
import os
import sys
hive_node_type = "HIVE"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
hivenodes = get_nodes_by_type("HIVE")
if (not hivenodes):
    report.fail("No hivenodes in the testbed ")
if len(hivenodes) == 1:
    report.fail("Only one Hive node available in TestBed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %hivenodes) 	
filelist = []
diffkeys = []
base_folder = hivenodes[0]
filelist=obj_parser.createfilelist(configdict,hive_node_type)
for filename in filelist:
	for node_alias in hivenodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + hive_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)

### Checking the difference in configs ###

folder = os.listdir(USER_OUTPUT_DIR + "/" + hive_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + hive_node_type + "/" + folder):
	list_folder = os.listdir(USER_OUTPUT_DIR + "/" + hive_node_type)
	for element in obj_parser.diff_func_xml(file,list_folder,hive_node_type,base_folder):
                diffkeys.append(element)
logger.info("Difference found in keys list is %s:" %diffkeys)
if len(diffkeys) == 0:
	logger.info("No diff found in Hive configs")
#### Printing the final result ###
else:
	logger.info("Difference found in parameters, list of parameters are %s:" %diffkeys)
	difffile = obj_parser.printdiff(diffkeys,"hive_configs")
        report.fail("Diff found in hive configs among nodes (%s).Please check the difffile (%s)" % (hivenodes,difffile))
