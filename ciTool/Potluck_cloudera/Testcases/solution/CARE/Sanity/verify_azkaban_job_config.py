"""
Purpose
=======
    Check that azkaban job config is present on master and standby namenodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import USER_OUTPUT_DIR
import os
import sys
azkaban_node_type = "AZKABAN"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
azkabannodes = get_nodes_by_type("AZKABAN")
if (not azkabannodes):
    report.fail("No azkabannodes in the testbed ")
if len(azkabannodes) == 1:
    report.fail("Only one Azkaban node available in Testbed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %azkabannodes)
filelist = []
base_folder = azkabannodes[0]
diffkeys = []
filelist=obj_parser.createfilelist(configdict,"AZKABAN_PROJECT")
rootdir = filelist[0]
azkaban_job_configs = azkaban_node_type + "_" + "JOB" 
print "rootdir is ",rootdir
for node_alias in azkabannodes:
	dest_dir_new = USER_OUTPUT_DIR + "/" + azkaban_job_configs + "/" + node_alias + "/"
	if not os.path.exists(dest_dir_new):
		os.makedirs(dest_dir_new)
	node = connect(node_alias)
        node.copyRecursiveToLocal(rootdir,dest_dir_new)	
folder = os.listdir(USER_OUTPUT_DIR + "/" + azkaban_job_configs + "/")[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + azkaban_job_configs + "/" + folder + "/"):
        list_folder = os.listdir(USER_OUTPUT_DIR + "/" + azkaban_job_configs + "/")
        for element in obj_parser.diff_func(file,list_folder,azkaban_job_configs,base_folder):
                diffkeys.append(element)
logger.info("Difference found in keys list is %s:" %diffkeys)
if len(diffkeys) == 0:
        logger.info("No diff found in Azkaban job configs")
else:
        logger.info("List of difference parameters is (%s):" %diffkeys)
        difffile = obj_parser.printdiff(diffkeys,"azkaban_job")
        report.fail("Diff found in azkaban job configs among nodes (%s).Please check the difffile: (%s)" % (azkabannodes,difffile))


