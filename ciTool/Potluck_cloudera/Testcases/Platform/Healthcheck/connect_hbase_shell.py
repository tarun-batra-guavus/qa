"""
Purpose
=======
    Check that hbase db is connecting and hbase shell commands are running fine

"""

from potluck.nodes import connect, get_nodes_by_type, get_db_dir
from potluck.logging import logger
from potluck.reporting import report
from potluck.healthcheck import healthcheck

hbasenodes = get_nodes_by_type("HMASTER")
if (not hbasenodes):
    report.fail("No HBASE nodes in the testbed ")
dbdir = "/usr/bin/hbase"
for node_alias in hbasenodes:
	node = connect(node_alias)
        flag = node.connecthbasedb(node_alias,dbdir)
        if flag ==1:
                logger.info("Hbase db is connecting")
        else:
                report.fail("Hbase db is not running on node %s" %node_alias)
