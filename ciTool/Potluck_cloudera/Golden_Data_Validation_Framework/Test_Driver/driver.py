from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import threading
import argparse
import re
import cgi
import json
import re
import os
import sys
sys.path.insert(0, ("/").join(os.getcwd().split("/")[0:-1]) + "/" + "Modules")
import datetime
import time
import subprocess
import subprocess as sub             
from email_module import Reporting


class RunTest(object):

    def __init__(self):
        self.tooldir = ("/").join(os.getcwd().split("/")[0:-1])
        self.test_to_parse  = []
    try:
        if sys.argv[1] == "-h":
            print "Help: \n Arguments to run the Driver \n 1. Current Version \n 2. Email Address"
            sys.exit(1)
        if sys.argv[1] == "" or sys.argv[2] == "":
            print "Help: \n Arguments to run the Driver \n 1. Current Version \n 2. Email Address"
    except IndexError:
        print "Help: \n Arguments to run the Driver \n 1. Current Version \n 2. Email Address"
        sys.exit(1)

    def configFileRead(self,filename):
        lines = ""
        try: 
            f = open(filename)
            lines = f.readlines()
            f.close()
        except IOError:
            print "Exitting as File not found"
            sys.exit()
        return(lines)

    def getCommandOutput(self,command):
        p = sub.Popen(command,stdout=subprocess.PIPE, shell=True)
        output, errors = p.communicate()
        #print output, errors
        return(output,errors)
            

    def cleanupPreviousExecution(self):
        epoch_time = int(time.time())
        self.getCommandOutput("mv " + self.tooldir + "/Test_Reports/Test_Execution_Current " + self.tooldir + "/Test_Reports/Test_Execution_" + str(epoch_time))
        self.getCommandOutput("mkdir " + self.tooldir + "/Test_Reports/Test_Execution_Current")
        self.getCommandOutput("rm -rf " + self.tooldir + "/Tmp/*" )

        
    def createJobExecutionList(self):
        job_name = []
        config_lines =  self.configFileRead(self.tooldir  + "/Config/test_selection.csv")
        print config_lines
        for line in config_lines:
            if "#" not in line and (line.split(",")[1].strip() == "Y" or line.split(",")[1].strip() == "y"):
                job_name.append(line.split(",")[0])
                print "Adding job: " + line.split(",")[0]
        return(job_name)

 
        
    def executeJob(self,db_version):
        joblist = self.createJobExecutionList()
        dict_job_status = {}
        
        for job in joblist:
            print "Executing job " + job
            subprocess.call("python " +  self.tooldir + "/Test_Scripts/" + job + " " + db_version, shell=True)
            #dict_job_status[job] = "Passed"
        
        #print dict_job_status
        

class HTTPRequestHandler(BaseHTTPRequestHandler):

    def getEmailFromQuery(self):
        e_mail = ""
        e_mail = self.path.split("&Email=")[1].split('&')[0].strip()
        e_mail = e_mail.replace("%40","@")
        e_mail = e_mail.replace("%2C",",")
        print e_mail
        return(e_mail)
 
    def getReqDetails(self):
        request_id = self.get_email_from_query()
        request_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        print str(request_id) + "-" + str(request_date)
        return(str(request_id) + "-" + str(request_date))


    def doGet(self):

        if "?" not in self.path or "/" not in self.path:
            self.send_response(400, 'MALFORMED REQUEST')
            return

        
	output = self.get_command_output("ps -ef | grep py")
        
        if "Job_" in output:
            self.send_header('Content-type','application/text')
            self.end_headers()
            self.send_response(200,'Automation Suite Already Running, Please try again once current execution is complete')
            return
        
        old_release = self.get_old_release_from_query()
        new_release = self.get_new_release_from_query()
        selection_list = []
        selection_list = self.get_selectionlist_from_query()
        email = self.get_email_from_query()
        req_id = self.get_req_details()

        self.send_header('Content-type','application/text')
        self.end_headers()
        self.send_response(200,'Automation Suite Started successfully, the report would be mailed to e-mail: ' + email)
        print "starting suite now"
        self.finish()
        self.connection.close()
        '''
        for selection in selection_list:
                current_day_str = time.strftime('%Y-%m-%d', time.localtime())
		if selection == '1':
                        file = "/data/Script_Report/execution/Execution_report_dump_Inclusion_job-" + current_day_str
                        print "Testing InclusionListCopy job"
                        f = open(file ,'w')
                        f.write("Starting execution_report_dump_Inclusion_job")
                        subprocess.call(" python /data/Script_Report/Job_InclusionListCopy.py 1 >> %s"%file, shell=True)
                        f.close()
                        subprocess.call("python /data/Script_Report/executionreport_parser_mailer.py" + " " + file + " " + email + " " + "InclusionListCopy_job" + " " + old_release + " " + new_release + " " + req_id, shell=True)


	'''	
        return
     
    def doPost(self):
        self.send_response(400, 'Server Does not supports POST request')
        return
 
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
 
    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)
 
class SimpleHttpServer():
    def __init__(self, ip, port):
        self.server = ThreadedHTTPServer((ip,port), HTTPRequestHandler)
 
    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
     
    def waitForThread(self):
        self.server_thread.join()
 
    def stop(self):
        self.server.shutdown()
        self.waitForThread()

obj_executor = RunTest()
obj_executor.cleanupPreviousExecution()
obj_executor.executeJob(sys.argv[1])
obj_emailer = Reporting()
obj_emailer.parseReports(sys.argv[1],sys.argv[2])

'''
if __name__=='__main__':

    
     parser = argparse.ArgumentParser(description='HTTP Server')
     parser.add_argument('port', type=int, help='Listening port for HTTP Server')
     parser.add_argument('ip', help='HTTP Server IP')
     args = parser.parse_args()
     
     server = SimpleHttpServer(args.ip, args.port)
     print 'Server is up and Running...........'
     server.start()
     server.waitForThread()
'''
