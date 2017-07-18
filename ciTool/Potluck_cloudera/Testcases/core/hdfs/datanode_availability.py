"""
Purpose
=======
    Check that all the data nodes are available

Test Steps
==========
    1. Login to master Namenode
    2. Execute ``hadoop dfsadmin -report``
    3. Check that the number of total nodes should be equal to the number of available nodes
"""
from potluck.nodes import connect_multiple, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from lib.node import find_master

namenode_alias_list = get_nodes_by_type("namenode")

namenodes = connect_multiple(namenode_alias_list)

# Find which node is TM Master
master_namenode = find_master(namenodes)

logger.info("Checking dn availability for %s" % master_namenode)

# Connect to the device and get a node object
logger.info("Checking master datanode availability")
hdfs = master_namenode.getHdfsReport()
if hdfs["AvailableNodes"] != hdfs["TotalNodes"]:
   report.fail("One or more Data Nodes is down")
else:
   logger.info("All the data nodes are up")
