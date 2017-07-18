"""
Purpose
=======
    Check rw permission on SAN partitions on each datanode

Test Steps
==========
    1. Login to datanode machine
    2. Goto shell prompt
    3. Execute `mount` command
    4. Check that the SAN storage should have `rw` permissions
"""
from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from lib.node import find_master
import re

datanodes = get_nodes_by_type("DATANODE")
for node in datanodes:
    # Connect to the device and get a node object
    dn1 = connect(node)
    logger.info("Checking read write permission on the san partition mounted on data node")
    dn1.setMode("shell")
    output = dn1.sendCmd("mount | grep -i hadoop-admin | grep -v grep", ignoreErrors=True)

    if not output:
        logger.info("SAN storage is not mounted on data node")
    else:
        if not re.search("rw", output, re.I):
            report.fail("san partition mounted on data node has not read/write permission")
        else:
            logger.info("san partition mounted on data node has read/write permission")
