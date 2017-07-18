"""
Purpose
=======
    Verify that Talend config is same on all talend nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import *
import os
import sys
talend_node_type = "TALEND"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
print "configdict is :" , configdict
talendnodes = get_nodes_by_type("TALEND")
#dest_dir = "/var/www/html/Potluck_cloudera/useroutput/"
if (not talendnodes):
    report.fail("No talendnodes in the testbed ")
if len(talendnodes) == 1:
    report.fail("Only one Talend node mentioned in TestBed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %talendnodes)
filelist = []
base_folder = talendnodes[0]
diffkeys = []
filelist=obj_parser.createfilelist(configdict,talend_node_type)

### Copy file to local server ####
for filename in filelist:
	print "filename is :",filename
	for node_alias in talendnodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + talend_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)

### Checking the difference in configs ###

folder = os.listdir(USER_OUTPUT_DIR + "/" + talend_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + talend_node_type + "/" + folder):
	list_folder = os.listdir(USER_OUTPUT_DIR + "/" + talend_node_type)
	for element in obj_parser.diff_func(file,list_folder,talend_node_type,base_folder):
		diffkeys.append(element)	
if len(diffkeys) == 0:
        logger.info("No diff found in Talend job configs")
else:
	logger.info("List of difference parameters is (%s):" %diffkeys)
	difffile = obj_parser.printdiff(diffkeys,"talend_configs")
        report.fail("Diff found in talend configs among nodes (%s).Please check the difffile (%s)" % (talendnodes,difffile))
