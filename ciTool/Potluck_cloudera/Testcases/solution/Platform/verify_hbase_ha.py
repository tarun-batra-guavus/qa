"""
Purpose
=======
    Check that Hbase Master HA on its respective Nodes

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -kf | grep "component"" and check that Hbase Master HA
"""
from time import sleep
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
hbasemaster = get_nodes_by_type("HMASTER")
hbaseregion = get_nodes_by_type("HREGION")
dbdir = "/usr/bin/hbase"

print "Hbase Master nodes are" , hbasemaster
print "Hbase Region nodes are" , hbaseregion
if (not hbasemaster):
    report.fail("No Hbase Master nodes in the testbed ")
if (not hbaseregion):
    report.fail("No HBASE REGION Servers in the testbed ")

for node_alias in hbasemaster:
    logger.info("Checking that Hbase Master is Running on machines")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"hbase-master")
    if flag ==1:
        logger.info("Hbase Master is Running on %s Node"%node_alias)
	logger.info("Reloading %s Node"%node_alias)
	node.reboot()
### Sleeping for 5 minutes so that HMASTER process runs again ###
	sleep(120)
	flag_1 = node.grepProcess(node_alias,"hbase-master")
	if flag_1 ==1:
		logger.info("%s Node Reloaded and HMASTER is running on it"%node_alias)
		flag_2 = node.connecthbasedb(node_alias,dbdir)
		if flag_2 ==1:
                	logger.info("Hbase db is connecting")
        	else:
                	report.fail("Hbase db is not running on node %s" %node_alias)
	else:
		report.fail("%s Node Reloaded and HMASTER is not running on it"%node_alias)
    else:
        report.fail("Hbase Master is not Running")

for node_alias in hbaseregion:
    logger.info("Checking that Hbase Region is Running on machines")
    node = connect(node_alias)
    flag = node.grepProcess(node_alias,"hbase-region")
    if flag ==1:
        logger.info("Hbase Region is Running on %s Node"%node_alias)
        logger.info("Reloading %s Node"%node_alias)
        node.reboot()
### Sleeping for 5 minutes so that HREGION process run's again ###
        sleep(120)
        flag_1 = node.grepProcess(node_alias,"hbase-region")
        if flag_1 ==1:
                logger.info("%s Node Reloaded and HREGION is running on it"%node_alias)
        else:
                report.fail("%s Node Reloaded and HREGION is not running on it"%node_alias)
    else:
        report.fail("Hbase Region is not Running")

