"""
Purpose
=======
    Check that Systemd Linked process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that Systemd Linked process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import sys
systemdnodes = get_nodes_by_type("SYSTEMD")
if (not systemdnodes):
    report.fail("No Systemd Linked node in the testbed ")

for node_alias in systemdnodes:
    logger.info("Checking that Systemd Linked process is running")
    node = connect(node_alias)
    max_wait_time = 0
    process_list = node.run_cmd("ls -lhaF /etc/systemd/system/ | grep ^- | grep -i \".service\" | awk -F \" \" '{print $9}'").split('\r\n')
    print "##################################"
    print "Process List :%s"%process_list
    print "##################################"
    for process in process_list[0:((len(process_list))-1)]:
	print "Process :%s"%process
	print "##################################"
	restart_time = node.run_cmd("cat /etc/systemd/system/%s | grep -i \"RestartSec\" | awk -F \"=\" '{print $2}'"%process).split('\r\n')
	print "##################################"
	print "Timeout :%s"%restart_time
	print "##################################"
	if restart_time > max_wait_time:
		max_wait_time = restart_time
    print "Max Sleep Time:%s"%float(max_wait_time[0])
    flag = node.systemd_linked_process_HA(process_list[0:((len(process_list))-1)],max_wait_time[0])
    if flag ==1:
        	logger.info("Systemd Linked process is running on %s node"%node_alias)
    else:
      		report.fail("Systemd Linked process is not running on node %s" %node_alias)
