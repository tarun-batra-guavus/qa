"""
Purpose
=======
    Check that hbase process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that hmaster and regionserver  process is in running state
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
from settings import USER_OUTPUT_DIR
import os
import sys
systemd_node_type = "SYSTEMD"
obj_parser = parser()
configdict = obj_parser.parse_config_file()
namenodes = get_nodes_by_type("NAMENODE")
diffkeys = []
if (not namenodes):
    report.fail("No namenodes in the testbed ")
if len(namenodes) == 1:
    report.fail("Only one Azkaban node mentioned in Testbed,difference of configs cannot be taken ")
logger.info("Config Difference to be taken among nodes (%s)" %namenodes)
filelist = []
base_folder = namenodes[0]
diffkeys = []
filelist=obj_parser.createfilelist(configdict,"SYSTEMD")
rootdir = filelist[0]
for node_alias in namenodes:
        dest_dir_new = USER_OUTPUT_DIR + "/" + systemd_node_type + "/" + node_alias + "/"
        if not os.path.exists(dest_dir_new):
                os.makedirs(dest_dir_new)
        node = connect(node_alias)
        node.copyRecursiveToLocal(rootdir,dest_dir_new)
folder = os.listdir(USER_OUTPUT_DIR + "/" + systemd_node_type + "/")[0]
for file in os.listdir(USER_OUTPUT_DIR + "/" + systemd_node_type + "/" + folder + "/"):
        list_folder = os.listdir(USER_OUTPUT_DIR + "/" + systemd_node_type + "/")
        for element in obj_parser.diff_func(file,list_folder,systemd_node_type,base_folder):
                diffkeys.append(element)
logger.info("Difference found in keys list is %s:" %diffkeys)
if len(diffkeys) == 0:
        logger.info("No diff found in Azkaban job configs")
else:
        logger.info("List of difference parameters is (%s):" %diffkeys)
        difffile = obj_parser.printdiff(diffkeys,"systemd_job")
        report.fail("Diff found in systemd job configs among nodes (%s).Please check the difffile: (%s)" % (systemdnodes,difffile))

