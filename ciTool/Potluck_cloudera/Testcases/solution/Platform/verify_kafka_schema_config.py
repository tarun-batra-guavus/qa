"""
Purpose
=======
    Verify that kafka-schema config is same on all kafka-schema nodes

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import USER_OUTPUT_DIR
import os
import sys
kafka_node_type = "KAFKA-SCHEMA"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
print "configdict is :" , configdict
kafkanodes = get_nodes_by_type("KAFKA-SCHEMA")
base_folder = kafkanodes[0]
print "base_folder",base_folder
diffkeys = []
if (not kafkanodes):
    report.fail("No Kafka  nodes in the testbed ")
if len(kafkanodes) == 1:
    report.fail("Only one Kafka node mentioned in TestBed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %kafkanodes)
filelist = []
filelist=obj_parser.createfilelist(configdict,kafka_node_type)
for filename in filelist:
	for node_alias in kafkanodes:
		dest_dir_new = USER_OUTPUT_DIR + "/" + kafka_node_type + "/" + node_alias + "/"
		if not os.path.exists(dest_dir_new):
    			os.makedirs(dest_dir_new)
		node = connect(node_alias)
		dest_file = dest_dir_new + filename.split("/")[-1]
		node.copyToLocal(filename,dest_file)
folder = os.listdir(USER_OUTPUT_DIR + "/" + kafka_node_type)[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + kafka_node_type + "/" + folder):
        list_folder = os.listdir(USER_OUTPUT_DIR + "/" + kafka_node_type)
        for element in obj_parser.diff_func(file,list_folder,kafka_node_type,base_folder):
                diffkeys.append(element)
logger.info("Difference found in keys list is %s:" %diffkeys)
if len(diffkeys) == 0:
        logger.info("No diff found in Kafka configs")
#### Printing the final result ###
else:
        logger.info("List of difference parameters is (%s):" %diffkeys)
        difffile = obj_parser.printdiff(diffkeys,"kafka_configs")
        report.fail("Diff found in Kafka schema registery configs among nodes (%s).Please check the difffile (%s)" % (kafkanodes,difffile))
