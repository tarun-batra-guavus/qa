"""
Purpose
=======
    Check that rpm version is same on all machines

"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
import sys
from potluck.parsing import parser
obj_parser = parser()
clusternodes = []
tmpdict = {}
rpmdict = {}
diffkeys = []

namenodes = get_nodes_by_type("NAMENODE")
datanodes = get_nodes_by_type("DATANODE")
clusternodes.append(namenodes)
clusternodes.append(datanodes)
print "clusternodes are :",clusternodes
if (not clusternodes):
    report.fail("No nodes in the testbed ")

for node_alias in clusternodes:
	for ip in node_alias:
		node = connect(ip)
		output = node.run_cmd("rpm -qa")
		output = output.split("\n")
		key = ip + "_rpm"
		value = str(output)
		tmpdict[key] = value
		rpmdict[str(ip)] = tmpdict.copy()
base_node = namenodes[0]
for node_alias in clusternodes:
	for ip in node_alias:
		logger.info("==================================================")
		logger.info("Comparing rpm version between node %s and %s" %(base_node,ip))
		for element in (obj_parser.comparedict1(rpmdict[base_node], rpmdict[ip])):
			diffkeys.append(element)
		logger.info("Difference found is: %s" %(diffkeys))
list_keys_unique = set(diffkeys)
if len(list_keys_unique) == 0:
	logger.info("No difference found in rpm versions between nodes")
else:
        report.fail("Diff found in rpm version (%s) between nodes" %(list_keys_unique))
