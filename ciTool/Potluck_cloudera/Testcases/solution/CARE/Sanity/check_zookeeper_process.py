"""
Purpose
=======
    Check that zookeeper process is running on all zookeeper nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

zookeepernodes = get_nodes_by_type("ZOOKEEPER")
print "zookeepernodes are" , zookeepernodes
if (not zookeepernodes):
    report.fail("No ZOOKEEPER nodes in the testbed ")
result_dict = {}
report_str = ""
for node_alias in zookeepernodes:
    logger.info("Checking that ZOOKEEPER process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"Dzookeeper")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
        if value == 1:
                logger.info("Zookeeper is running on node %s" %key)
        elif report_str == "":
                report_str = key
        else:
                report_str = report_str + "," + key
if report_str == "" :
	logger.info("Zookeeper process is running on nodes")
else:
        report.fail("Zookeeper process is not running on nodes: %s" %report_str)
