"""
Purpose
=======
    Verify that hbase config is same on all HMASTER nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import USER_OUTPUT_DIR
import os
import sys
hbase_node_type = "HMASTER"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
hbasenodes = get_nodes_by_type("HMASTER")
dest_dir = "/var/www/html/Potluck_cloudera/useroutput/"
if (not hbasenodes):
    report.fail("No hbasenodes in the testbed ")
if len(hbasenodes) == 1:
    report.fail("Only one Hbase node available in TestBed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %hbasenodes)
filelist = []
base_folder = hbasenodes[0]
diffkeys = []
filelist=obj_parser.createfilelist(configdict,hbase_node_type)
for filename in filelist:
	print "filename is :",filename
	for node_alias in hbasenodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + hbase_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)

### Checking the difference in configs ###

folder = os.listdir(USER_OUTPUT_DIR + "/" + hbase_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + hbase_node_type + "/" + folder):
	list_folder = os.listdir(USER_OUTPUT_DIR + "/" + hbase_node_type)
	for element in obj_parser.diff_func_xml(file,list_folder,hbase_node_type,base_folder):
		diffkeys.append(element)
if len(diffkeys) == 0:
        logger.info("No diff found in Hbase configs among nodes (%s)" %hbasenodes)
#### Printing the final result ###
else:
	logger.info("List of difference parameters is %s:" %diffkeys)
        difffile = obj_parser.printdiff(diffkeys,"hbase_configs")
        report.fail("Diff found in hbase configs among nodes (%s).Please check the difffile (%s)" % (hbasenodes,difffile))

