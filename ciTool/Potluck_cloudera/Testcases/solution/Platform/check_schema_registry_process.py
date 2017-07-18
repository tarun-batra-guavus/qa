"""
Purpose
=======
    Check that Schema-Registry process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Schema-Registry process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report

schema_registry_nodes = get_nodes_by_type("SCHEMA-REGISTRY")
if (not schema_registry_nodes):
    report.fail("No Schema-Registry node in the testbed ")

for node_alias in schema_registry_nodes:
    logger.info("Checking that Schema-Registry process is running")
    node = connect(node_alias)
    flag = node.systemctlProcess("SCHEMA-REGISTRY")
    if flag ==1:
        logger.info("Schema-Registry process is running on %s node"%node_alias)
    else:
      	report.fail("Schema-Registry process is not running on node %s" %node_alias)
