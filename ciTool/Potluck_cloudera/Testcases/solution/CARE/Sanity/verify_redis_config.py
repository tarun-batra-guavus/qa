"""
Purpose
=======
    Verify that redis config is same on all redis nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import *
import os
import sys
redis_node_type = "REDIS"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
print "configdict is :" , configdict
redisnodes = get_nodes_by_type("REDIS")
diffkeys = []
if (not redisnodes):
    report.fail("No Redis  nodes in the testbed ")
if len(redisnodes) == 1:
    report.fail("Only one Redis node mentioned in TestBed,difference of configs cannot be taken ")
base_folder = redisnodes[0]
logger.info("Config Difference to be taken among nodes (%s)" %redisnodes)
filelist = []
filelist=obj_parser.createfilelist(configdict,redis_node_type)


### Copy files from Remote Machine to Local server ####
for filename in filelist:
	for node_alias in redisnodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + redis_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)
folder = os.listdir(USER_OUTPUT_DIR + "/" + redis_node_type)[0]

### Find list of config parameters in which difference exist ###
for file in os.listdir(USER_OUTPUT_DIR + "/" + redis_node_type + "/" + folder):
        list_folder = os.listdir(USER_OUTPUT_DIR + "/" + redis_node_type)
        for element in obj_parser.diff_func_text(file,list_folder,redis_node_type,base_folder):
                diffkeys.append(element)
logger.info("Difference found in keys list is %s:" %diffkeys)
if len(diffkeys) == 0:
        logger.info("No diff found in Redis configs")
#### Printing the final result ###
else:
        logger.info("List of difference parameters is (%s):" %diffkeys)
        difffile = obj_parser.printdifftxt(diffkeys,"redis_configs")
        report.fail("Diff found in Redis configs among nodes (%s).Please check the difffile (%s)" % (redisnodes,difffile))
