from potluck.reporting import report
from potluck.nodes import connect, get_nodes_by_type
import re
class checkpsql():
	def checkProcess():
		output = node.sendCmd("service postgresql status", ignoreErrors=True)
    		if not re.search(r"active \(running\)", output, re.I):
			return(0)
    		else:
			return(1)
		
