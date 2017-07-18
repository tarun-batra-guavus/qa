"""
Purpose
=======
    Check that tomcat process is running on all Tomcat machines

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
tomcatnodes = get_nodes_by_type("TOMCAT")
print "tomcatnodes are" , tomcatnodes
if (not tomcatnodes):
    report.fail("No tomcat nodes in the testbed ")
result_dict = {}
report_str = ""
for node_alias in tomcatnodes:
    logger.info("Checking that Tomcat process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"apache-tomcat")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Tomcat process is running on node %s" %key)
	elif report_str == "":
		report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
        logger.info("Tomcat process is running on nodes")
else:
        report.fail("Tomcat process is not running on nodes: %s" %report_str)
