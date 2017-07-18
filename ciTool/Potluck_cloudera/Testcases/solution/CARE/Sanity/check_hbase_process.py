"""
Purpose
=======
    Check that hbase process is running on all hbase(HMASTER/HREGION) nodes

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

hbasemaster = get_nodes_by_type("HMASTER")
hbaseregion = get_nodes_by_type("HREGION")
if (not hbasemaster):
    report.fail("No HBASE  MASTER in the testbed ")
if (not hbaseregion):
    report.fail("No HBASE REGION Servers in the testbed ")
result_dict = {}
report_str = ""
for node_alias in hbasemaster:

    logger.info("Checking that HBASE Master process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"Hmaster")
    result_dict[node_alias] = flag

for node_alias in hbaseregion:
    logger.info("Checking that HBASE region server process is running")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"HRegionServer")
    result_dict[node_alias] = flag
for key,value in result_dict.iteritems():
	print "key",key
	if value == 1:
		logger.info("Hbase process is running on node %s" %key)
        elif report_str == "":
		report_str = key
	else:
                report_str = report_str + "," + key
if report_str == "" :
	logger.info("Hbase  process is running on all nodes")
else:
	report.fail("Hbase process is not running on nodes: %s" %report_str)

