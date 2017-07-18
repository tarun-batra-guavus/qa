"""
Purpose
=======
    Check that all the namenode processes are running

"""
from potluck.nodes import connect_multiple, get_nodes_by_type, connect
from potluck.logging import logger
from potluck.reporting import report
from lib.node import find_master

# Find which collector is TM Master
namenode_alias_list = get_nodes_by_type("namenode")
if (not namenode_alias_list):
    report.fail("No namenodes in the testbed ")
# Check namenode processes
logger.info("Checking that all name node processes are running")
for namenodes in namenode_alias_list:
    node = connect(namenodes)
    output_1=node.checkserviceProcess("hadoop-hdfs-namenode.service")
    output_2=node.checkserviceProcess("hadoop-yarn-resourcemanager.service")
    if output_1==1 and output_2==1:
   	logger.info("All the NameNode processes are running on namenode %s" %namenodes)
    else:
   	report.fail("One or more Name Node processes is not running on namenode %s" %namenodes)
