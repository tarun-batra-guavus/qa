import re
from potluck.nodes import *
from potluck.logging import logger
from potluck.reporting import report
from potluck import utils, env
import time
import re
import threading
globalCount = 0

class myThread (threading.Thread):
    def __init__(self,node,pass_string,fail_string,timeWait = -1):
        threading.Thread.__init__(self)
        self.node = node
        self.pass_string = pass_string
        self.fail_string = fail_string
        self.result_status = ""
        self.result_reason = ""
        self.timeWait = timeWait
       
    def run(self):
        if not self.timeWait == -1 :
            self.result_status,self.result_reason = MonitorLogs(self.node,self.pass_string,self.fail_string,self.timeWait)
        else :
            self.result_status,self.result_reason = MonitorLogs(self.node,self.pass_string,self.fail_string)
        

def PathCombine(tool_path,zipped_tool_dest_path):
	path_src = ""
	path_dest = ""
	pathlist = tool_path.split("/")
	for i in pathlist :
	 path_src = path_src+"/"+i
	path_src = path_src+"/"

	pathlist = zipped_tool_dest_path.split("/")
	pathlist.pop()
	for i in pathlist :
	 path_dest = path_dest+"/"+i
	path_dest = path_dest+"/"
	
	path = path_dest+path_src
	
	path = re.sub("/+",'/',path)
	return path

def CreateSimulatorConfig(master_ip) :
	path = env.config.variables["conf_path"]
	Rubix_URL = env.config.variables["Rubix_URL"]
	Requests_Path = env.config.variables["Requests_Path"]
	webxml = env.config.variables["webxml"]
	insta_host = env.config.variables["insta_host"]
	conf_path = env.config.variables["conf_path"]
	insta_port = env.config.variables["insta_port"]
	catlina_logs = env.config.variables["catlina_logs"]
	root_pwd = env.config.variables["root_pwd"]
	time_zone = env.config.variables["time_zone"]

	CF = open(conf_path,'w')
	CF.write("[Requests_Path] = "+Requests_Path+"\n")
	CF.write("[Tomcat_Web_Dir_Name] = test"+"\n")
	CF.write("[Rubix_URL] = "+Rubix_URL+"\n")
	CF.write("[Web_Xml_File_Path] = "+webxml+"\n")
	CF.write("[BASE64_Encrypted_Password] = admin@Admin@123/admin"+"\n")
	CF.write("[INSTA_HOST] = "+insta_host+"\n")
	CF.write("[INSTA_PORT] = "+insta_port+"\n")
	CF.write("[QUERY_WAIT_FREQUENCY] = 300"+"\n")
	CF.write("[CATALINA_LOGS] = "+catlina_logs+"\n")
	CF.write("[RUBIX_ROOT_PASSWORD] = "+root_pwd+"\n")
	CF.write("[XML_RPC_SERVER_PORT] = 8000"+"\n")
	CF.write("[TIME_ZONE] = "+time_zone+"\n")
	CF.write("[MACHINE_IP] = "+master_ip+"\n")
	CF.write("[EMAIL_ADDRESSES] = admin@guavus.com"+"\n")
	CF.write("[TIME_THRESHHOLD] = 2"+"\n")
	CF.close()


def DeploySimulator():
    zipped_tool_src_path = env.config.variables["zipped_tool_src_path"]
    zipped_tool_dest_path = env.config.variables["zipped_tool_dest_path"]
    tool_path = env.config.variables["tool_path"]
    os.system("tar czf "+zipped_tool_src_path+" "+env.config.variables["tool_path"]+" 2> /dev/null")
    master.copyFromLocal(zipped_tool_src_path,zipped_tool_dest_path )
    master.setMode("shell")
    master.sendCmd("tar -xvf "+zipped_tool_dest_path+" 1>/dev/null 2>/dev/null")


def RunSimulator(master,path):
	master.sendCmd("cd "+path+"InstaUtils")
	RESULT = master.sendCmd("python "+path+"InstaUtils/DataAvailability.py 2>/dev/null")
	RESULT = re.search("TOTAL PASS:\s(\d+)[\s\n]+TOTAL FAIL:\s(\d+)",RESULT)
	passed = int(RESULT.group(1))
	failed = int(RESULT.group(2))
	return (passed,failed)

def GetSimulatorPath():
	zipped_tool_dest_path = env.config.variables["zipped_tool_dest_path"]
	tool_path = env.config.variables["tool_path"]
	path = PathCombine(tool_path, zipped_tool_dest_path)
	return path

def RestartRubix(nodes):
	# Connect to all rubix nodes
    for node in nodes :
        mode = node.getMode()
        node.setMode("config")
        logger.info("Restarting rubix process on %s" % node)
        output = node.sendCmd("pm process rubix restart")
    
        # TODO: Confirm that rubix process restarted successfully
        node.setMode(str(mode))

	# Give the system some time to converge
        #time.sleep(60)

def RestartRubixCheck(pass_string,fail_string):
    pidList = []
    modeList = []
    threadList = []
    node_aliases = get_nodes_by_type("rubix")
    nodes = connect_multiple(node_aliases)
    pass_string = re.sub(",","|",pass_string)
    fail_string = re.sub(",","|",fail_string)
    string = pass_string+"|"+fail_string
    i = 0
    RestartRubix(nodes)
    globalCount = 0
    for node in nodes :
        threadList.append(myThread(node,pass_string,fail_string))
    for thread_count in threadList:
        thread_count.start()
    while ( threading.activeCount() != 1 ):
        time.sleep(60)
        print "Count: "+str(threading.activeCount())
    result_list = {}
    for node in range(len(node_aliases)) :
         result_list[str(node_aliases[node])+" "+str(threadList[node].result_status)] = threadList[node].result_reason
    return result_list



def LogChecker( nodes,pass_string,fail_string,timeWait = 1):
    result_list = {}
    threadList = []
    node_aliases = get_nodes_by_type("rubix")
    pass_string = re.sub(",","|",pass_string)
    fail_string = re.sub(",","|",fail_string)
    for node in nodes :
        threadList.append(myThread(node,pass_string,fail_string,timeWait))
    for thread_count in threadList:
        thread_count.start()
    while ( threading.activeCount() != 1 ):
        time.sleep(1)
    result_list = {}
    for node in range(len(node_aliases)) :
         result_list[str(node_aliases[node])+" "+str(threadList[node].result_status)] = threadList[node].result_reason
    return result_list

def MonitorLogs(node,pass_string,fail_string,timeWait = -1):
    log = ""
    ERROR_FLAG = 0
    last_log = ""
    node.pushMode("shell")
    app,instance = GetRubixProperty(node)
    path = "/data/instances/"+app+"/"+instance+"/bin/rubix.log"
    log = node.sendCmd("tac "+path+"|grep -iEm 1 \""+pass_string+"\"")
    error_log = node.sendCmd("tac "+path+"| grep -Em 1 \""+fail_string+"\"")
    last_error_log = error_log
    last_log = log
    while True :
        log = node.sendCmd("tac "+path+"|grep -iEm 1 \""+pass_string+"\"")
        error_log = node.sendCmd("tac "+path+"| grep -Em 1 \""+fail_string+"\"")
        print "Time left :"+str(timeWait)
        if not timeWait == -1 :
            timeWait = int(int(timeWait) - 1)
            if ( int(timeWait) == 0 ):
                break
        if (len(log) != 0 ):
            if ( str(log) != str(last_log) or str(error_log) != str(last_error_log) ):
                if ( str(error_log) != str(last_error_log) ) :
                    ERROR_FLAG = 1 
                    print "Error Logs:"+str(error_log)
                    print "Last Error Logs:"+str(last_error_log)
                print "log :"+str(log)+"\nlast_log :"+str(last_log)
                break
        time.sleep(60)
    node.popMode()
    if ERROR_FLAG == 0 :
        return '1',"passed"
    else : 
        return '-1',error_log
def GetRubixProperty(node) :

	'''
	returns the app and instance ( in the same order ) for a rubix node
	'''

	node.pushMode("config")
	
	output = node.sendCmd("rubix status")

	app = re.search('Application: (.*)',output)
	app = app.group(1)
	app = re.sub('\s','',app)

	instance = re.search("Instance: (.*)",output)
	instance = instance.group(1)
	instance = re.sub('\s','',instance)
	
	node.popMode()
	
	return app,instance
