"""
Purpose
=======
    Check that all the `datanode` processes are running on each datanode

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

node_alias_list = get_nodes_by_type("DATANODE")
if (not node_alias_list):
    report.fail("No datanodes nodes in the testbed ")
# Check datanode processes
for node_alias in node_alias_list:
    node = connect(node_alias)
    logger.info("Checking that all required processes are running on %s" % node)

    # Connect to the device and get a node object
    node.setMode("shell")

    #flag_1 = node.run_cmd("ps -aef | grep -i -- '-Dproc_datanode' | grep -v grep")
    #flag_2 = node.run_cmd("ps -aef | grep -i -- '-Dproc_nodemanager' | grep -v grep")
    flag_1 = node.grepProcess(node_alias,"Dproc_datanode")
    flag_2 = node.grepProcess(node_alias,"Dproc_nodemanager")
    if flag_1 and flag_2:
        logger.info("All the required processes are running on datanode %s" % node)
    else:
        report.fail("Nodemanager or Datanode process is not running on datanode '%s'" % node)
