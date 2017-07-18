"""
Purpose
=======
    Check that all the `journal` processes are running on each journal node

"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import re
node_alias_list = get_nodes_by_type("JOURNALNODE")
if (not node_alias_list):
    report.fail("No journalnodes nodes in the testbed ")

# Check journalnode process
for node_alias in node_alias_list:
    node = connect(node_alias)
    logger.info("Checking that all required processes are running on %s" % node)

    # Connect to the device and get a node object
    node.setMode("shell")

    # Check datanode processes
    #output = node.run_cmd("ps -aef | grep -i -- '-Dproc_journalnode' | grep -v grep")
    output = node.grepProcess(node_alias,"Dproc_journalnode")
    print "output is :",output
    if output == 1:
	logger.info("Journalnode processes are running on datanode %s" % node)
    else:
        report.fail("Journalnode process is not running on datanode '%s'" % node) 
'''   
    if len(re.findall(r"journalnode", output, re.IGNORECASE)) > 0:
        logger.info("All the required processes are running on datanode %s" % node)
    else:
        report.fail("Journalnode process is not running on datanode '%s'" % node)

'''
