from potluck.reporting import report
from potluck.logging import logger
from potluck.nodes import connect, get_nodes_by_type
from potluck.utils import diffxml
import re
ignorefile = "/var/www/html/ignore.txt"
class healthcheck(object):
	def checkserviceProcess(self,ipaddr,processname):
		logger.info("Monitoring of process %s" % processname)
    		# Connect to the device and get a node object
    		node = connect(ipaddr)
    		print "connection to device is successful"
    		logger.info("Checking that %s process is running" %processname)
    		node.setMode("shell")
		output = node.sendCmd("service " + processname +  " status", ignoreErrors=True)
    		if not re.search(r"active \(running\)", output, re.I):
			return(0)
    		else:
			return(1)
		
	def grepProcess(self,ipaddr,processname):
		logger.info("Monitoring of process %s" % processname)
    		# Connect to the device and get a node object
    		node = connect(ipaddr)
    		print "connection to device is successful"
    		logger.info("Checking that %s process is running" %processname)
    		node.setMode("shell")
		output = node.run_cmd("ps -ef | grep  -i " + processname + " | grep -v grep")
		print "output is :" , output
		if len(re.findall(r"%s" %processname, output, re.IGNORECASE)) > 0:
			return(1)
    		else:
			return(0)
	def verifyConfigs(self,ipaddrlist,fileName,nodetype):
		ip1 = ipaddrlist[0]
		ip2 = ipaddrlist[1]
		dest_dir = "/var/www/html/Potluck_cloudera/useroutput"
		for ip in ipaddrlist:
			ip = ip.strip("\n")
    			node = connect(ip)
    			node.setMode("shell")
			destfile = dest_dir + "_" + nodetype
			print "destfile is:" , destfile
    			node.copyToLocal(fileName,destfile)
    			#node.copyToLocal(fileName,dest_dir)
		filename1 = dest_dir + ip1
		filename2 = dest_dir + ip2
		print "filename1 is" ,filename1
		print "filename2 is" ,filename1
		logger.info("Matching the configuration between master and standby node")
		diff = diffxml(filename1,filename2,ignorefile)
		f = open(diff,"r")
		if len(f.readlines()) > 0:
			return(0)
		else:
			return(1)
	def connectDb(self,ipaddr,dbdir):
		
    		# Connect to the device and get a node object
    		node = connect(ipaddr)
    		print "connection to device is successful"
    		#logger.info("Checking that %s db is connecting" %dbname)
    		node.setMode("shell")
		print "printing now..."
		output = node.run_cmd(dbdir + " shell","0>")
		output = node.run_cmd("list","0>")
		print "hello1",output
		if re.search(r"hbase\(main\)", output, re.IGNORECASE):
			return(1)
    		else:
			return(0)
	def checkDatanodeavail(self,ipaddr):
		logger.info("Checking live and dead datanodes on master namenode")
    		# check if master node
    		node = connect(ipaddr)
    		node.setMode("shell")
		role =  node.isMaster()
    		print role
		#Run hdfs command to checkdatanode status
		
