from logger import Logger
import sys
import os
import subprocess
import subprocess as sub
import time
import re
import errno
import datetime
import pexpect
from datetime import datetime
import calendar
import threading
from utility_module import utility
import socket
import sys

class RegressionModule(utility):

    lines = None

    def __init__(self,schemaname):
        self.lines =  None
        self.header = "0"
        self.child = None
        self.col_to_remove = "timestamp"
        self.tooldir = ("/").join(os.getcwd().split("/")[0:-1])
        self.current_execution_folder = ("/").join(os.getcwd().split("/")[0:-1]) + "/Test_Reports/Test_Execution_Current/" + str(sys.argv[0].split("/")[-1].split(".py")[0])
        self.logger = Logger(str(sys.argv[0].split("/")[-1].split(".py")[0]),self.tooldir + "/Test_Reports/Test_Execution_Current/").get()
        #print self.logger
        self.ipaddress = None
        self.password = None
        self.username = None
        self.job_nohup_path = None
        self.job_path = None
        self.application_id = None
        self.datanode_ip = []
        self.impala_dump_path = self.current_execution_folder + "/" + "impala_db_dump_" + str(schemaname)
        self.hbase_dump_path = self.current_execution_folder + "/" + "HBASE_db_dump_" + str(schemaname)
        self.hive_dump_path = self.current_execution_folder + "/" + "HIVE_db_dump_" + str(schemaname)
        self.hive_cleaup_path = None
        self.hbase_cleaup_path = None
        self.impala_cleaup_path = None
        print self.tooldir 

    def getCommandOutput(self,command,expect = "#"):
        #print "Running command: " + command
        self.child.sendline(command)
        time.sleep(5)
        self.child.expect(expect)
        self.logger.info("Running command : " + command)
        #print self.child.before
        return(self.child.before)

    def getDnIpaddress(self):
        print "inside dn_ip"
        command = "hdfs dfsadmin -report | grep -iw Name > /tmp/dn_ip_file" 
        self.getCommandOutput(command)
        self.scpReceiveFromServer("/tmp/dn_ip_file",self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        time.sleep(2)
        f = open(self.tooldir + "/" + "Tmp/dn_ip_file",'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            if ":" in line:
                self.datanode_ip.append(line.split(":")[1].strip())
        self.logger.info("Data Nodes IP address: " + str(self.datanode_ip))
        print self.datanode_ip
        
        
    def connectToMachine(self,username,password,ip_address):
        '''
        Input
        username = user name of server
        password = password of server
        Output 
        child object that creates a session onto the server after performing login
        '''
        self.ipaddress = ip_address
        self.password  = password
        self.username = username
        #print self.username , self.ip_address , self.password
        ssh_newkey = 'Are you sure you want to continue connecting'
        self.child = pexpect.spawn('ssh %s@%s'%(username, ip_address))
        self.child.timeout = 3600
        expected_text = str(username) + "@" + str(ip_address) + "'s password:"
        #print expected_text
        i = self.child.expect([ssh_newkey,pexpect.TIMEOUT,pexpect.EOF,expected_text,'>','#'])
        #print i 
        if i == 0: # SSH does not have the public key. Just accept it.
            self.child.sendline ('yes')
            i = self.child.expect([ssh_newkey,pexpect.TIMEOUT,pexpect.EOF,expected_text,'>','#'])
            #print i
        if i == 1: # Invalid Cred or Servername
            self.logger.error('Server Down or not pingable')
            #return(1)
        if i == 2:
            self.logger.error('Invalid Username/Password')
            #return(1)
        if i == 3:
            self.child.sendline(password)
            i = self.child.expect(['#','>','$'])
            #print i
            if  i == 0 or i == 1:
                self.logger.error('Invalid Username/Password')
                #return(1)
        time.sleep(2)
        #print "self: ", self.child
        self.child.sendline("\n")
        self.child.expect(r"\[root\@[\.a-zA-Z0-9]+ [\~]+\]\#")
        self.logger.info("connection to " + ip_address + " successful")
        print "connection to " + ip_address + " successful"
        self.getDnIpaddress()

    def sleepTillHourBoundary(self):
        curr_time = int(time.time())
        print curr_time
        for i in range(1,3600):
            if (curr_time + i)%3600 == 0:
                print i
                return(i)       

    def returnTimeEpoch(self,filename):
        timestamp = int(int(self.sort_filenames(filename))/100)
        pattern = '%Y%m%d%H%M%S'
        epoch = int(time.mktime(time.strptime(str(timestamp), pattern)))
        return(epoch)

################### Impala Dumper ########################################################################

    def returnTableListImpala(self,schema_name):
        self.child.sendline("impala-shell -q \"use " + str(schema_name) + "; show tables;\"")
        self.child.expect("#")
        table = self.child.before
        table_list = table.split("\n")
        final_table_list = []
        for line in table_list:
            if "| " in line and "| name " not in line:
                final_table_list.append(line.strip().split("| ")[1].split(" |")[0].strip())
        self.logger.info("Impala Table List to Dump Tables: " + str(final_table_list))
        return(final_table_list)
        
    def dumpTablesImpala(self,schemaname):
        dict_table_count = {}
        tablelist = []
        threadlist = []
        child_nn = self.child
        self.connectToMachine("root","root@123",self.datanode_ip[0])
        tablelist = self.returnTableListImpala(schemaname)
        self.getCommandOutput("rm -rf /data/Test_Execution_Report/*")
        self.getCommandOutput("mkdir /data/Test_Execution_Report")
        self.getCommandOutput("mkdir /data/Test_Execution_Report/impala_db_dump_" + str(schemaname))
        for table in tablelist:
            self.dumpTableCommandImpala(schemaname,table)
            self.logger.info("Dumping impala table at location: /data/Test_Execution_Report/impala_db_dump_" + str(schemaname) + "/" + table)

        self.impala_cleaup_path = "/data/Test_Execution_Report/impala_db_dump_" + str(schemaname)
        self.impala_dump_path = self.current_execution_folder + "/" + "impala_db_dump_" + str(schemaname)
        self.scpReceiveFromServer("/data/Test_Execution_Report/impala_db_dump_" + str(schemaname) ,self.current_execution_folder,self.ipaddress,self.username,self.password)
        self.child = child_nn
                                      
    def returnImpalaTableCol(self,schema_name,tablename,col_to_remove):
        command = self.getCommandOutput("impala-shell -q \"use " + str(schema_name) + "; desc " +  str(tablename) + ";\"")
        col_list = []
        print command
        for line in command.splitlines():
            if "| name   " not in line and "|" in line:
                col_list.append(line.split("|")[1].strip())
        for col in col_list:
            if col in col_to_remove:
                col_list.remove(col)
        return(",".join(col_list))

    def dumpTableCommandImpala(self,schemaname,table):
        filename = "/data/Test_Execution_Report/impala_db_dump_" + str(schemaname) + "/" + str(table) + "_dump.txt"
        col_string = self.returnImpalaTableCol(schemaname,table,self.col_to_remove)
        command = "impala-shell -q \"use " +str(schemaname) + "; select " + str(col_string) + " from " + str(table) + ";\" -o  \"" + str(filename) + "\""
        self.logger.info("Impala data dump command for table: " + table + "is :" + command)
        self.getCommandOutput(command)
        

#######################################################################################################

###################Phoenix/HBASE dumper################################################################

        
    def returnTableListPhoenix(self,schemaname):
        phoenix_table_list = []
        self.createPhoenixQueryFile("!tables","/data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname) + "/" + "tables_file.txt",self.tooldir + "/" + "Tmp/table_list.txt")
        self.scpSendToSever(self.tooldir + "/" + "Tmp/table_list.txt","/tmp/",self.ipaddress,self.username,self.password)
        command = "python /root/phoenix-4.6.0-HBase-1.1-bin/bin/sqlline.py localhost /tmp/table_list.txt"
        self.getCommandOutput(command,"Closing:")
        self.getCommandOutput("\n")
        time.sleep(30)
        #print command
        #current_server_ip = socket.gethostbyname(socket.gethostname())
        print "Running scp Receive"
        self.scpReceiveFromServer("/data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname) + "/" + "tables_file.txt",self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        
        f = open(self.tooldir + "/" + "Tmp/tables_file.txt",'r')
        output = f.read()
        f.close()
        print output
        for line in output.splitlines():
            if schemaname.upper() in  line and "," in line: 
                print line
                phoenix_table_list.append(line.split("\',\'")[1].strip() + "." + line.split("\',\'")[2].strip())
        self.logger.info("HBASE Table List to be dumped: " + str(phoenix_table_list))
        return(phoenix_table_list)

    def colListForTableHbase(self,schemaname,tablename,col_to_ignore):
        self.createPhoenixQueryFile("!describe " + tablename," /data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname) + "/" + tablename + "_schema.txt",self.tooldir + "/" + "Tmp/" + tablename + "_schema.txt")
        self.scpSendToSever(self.tooldir + "/" + "Tmp/" + tablename + "_schema.txt" ,"/tmp/",self.ipaddress,self.username,self.password)
        command = "python /root/phoenix-4.6.0-HBase-1.1-bin/bin/sqlline.py localhost /tmp/" +  tablename + "_schema.txt"
        self.getCommandOutput(command,"Closing:")
        self.getCommandOutput("\n")
        time.sleep(20)
        #print command
        #current_server_ip = socket.gethostbyname(socket.gethostname())
        print "Running scp Receive from " + str(self.ipaddress)
        self.scpReceiveFromServer("/data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname) + "/" + tablename + "_schema.txt",self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        f = open(self.tooldir + "/" + "Tmp/" +  tablename + "_schema.txt",'r')
        output = f.readlines()
        f.close()
        print output
        col_list_hbase = []
        ignore_col_list = []
        for line in output:
            if ","  in line and "COLUMN_NAME" not in line and "Saving all output to" not in line and "!describe" not in line and  "Closing: org.apache.phoenix.jdbc.PhoenixConnection" not in line and "sqlline version" not in line:
                col_list_hbase.append(line.split(",")[3].replace("'","").strip())
        query_list = []
        if "," in col_to_ignore:
            ignore_col_list = col_to_ignore.split(",")
        else :
            ignore_col_list.append(col_to_ignore)

        ignore_col_list = map(lambda x:x.lower(),ignore_col_list)
        for line in col_list_hbase:
            
            if "Saving all output to" in line or "!describe" in line or "rows selected (" in line or "Closing: org.apache.phoenix.jdbc.PhoenixConnection" in line or "sqlline version" in line:
                continue
            #print "abhay" + line
            if line.strip().lower() not in ignore_col_list:
                query_list.append(line.strip().lower())
        print query_list
        return(",".join(query_list))


    def runCommandCurrentServer(self,command):
        p = sub.Popen(command,stdout=subprocess.PIPE, shell=True)
        output, errors = p.communicate()
        return(output)

    def dumpTablesPhoenix(self,schemaname,col_to_ignore,custom_sleep=60):
        table_list = []
        self.getCommandOutput("mkdir /data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname))
        table_list = self.returnTableListPhoenix(schemaname)
        if table_list == []:
            self.logger.error("HBASE DB tables not found for schema " + schemaname + ", exiting the current flow")
            sys.exit(1)
        dump_path = ""
        sed_command = "sed -i -e \'1,2d\' -n -e :a -e \'1,5!{P;N;D;};N;ba\' "
        for table in table_list:
            dump_path = "/data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname) + "/" +  str(table.split(".")[1]) + ".txt"
            self.createPhoenixQueryFile("select " + self.colListForTableHbase(schemaname,table,col_to_ignore) + " from " + str(table),dump_path,self.tooldir + "/" + "Tmp/table.txt")
            self.scpSendToSever(self.tooldir + "/" + "Tmp/table.txt","/tmp/" ,self.ipaddress,self.username,self.password)
            command = "python /root/phoenix-4.6.0-HBase-1.1-bin/bin/sqlline.py localhost /tmp/table.txt"
            self.getCommandOutput(command,"Closing: org.apache.phoenix.jdbc.PhoenixConnection")
            time.sleep(custom_sleep)
            self.getCommandOutput(sed_command + dump_path)
            time.sleep(5)
        self.logger.info("Phoenix tables dumped at location: " + str(dump_path))
        self.hbase_dump_path = self.current_execution_folder + "/" + "HBASE_db_dump_" + str(schemaname)
        self.hbase_cleaup_path = "/data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname)
        self.scpReceiveFromServer("/data/Test_Execution_Report/HBASE_db_dump_" + str(schemaname) ,self.current_execution_folder,self.ipaddress,self.username,self.password)

    def createPhoenixQueryFile(self,query,csv_output_filename,filename):
        f = open(filename,"w")
        f.write("!outputformat csv")
        f.write("\n")
        f.write("!record " + str(csv_output_filename))
        f.write("\n")
        f.write(query)
        f.write("\n")
        f.close()
        self.logger.info("phoenix query file created successfully")

##########################################################################################################

########################################HIVE##############################################################

    def returnTableListHive(self,schemaname):
        hive_table_list = []
        command = "hive -e \"use " + schemaname + "; show tables;\" > /data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/table_list.txt"
        self.getCommandOutput(command,"Time taken:")
        self.getCommandOutput("\n")
        print command
        self.scpReceiveFromServer("/data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" + "table_list.txt",self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        f = open(self.tooldir + "/" + "Tmp/table_list.txt",'r')
        output = f.read()
        f.close()
        print output
        #sys.exit()
        for line in output.splitlines():
            hive_table_list.append(line.strip())
        self.logger.info("Dumping the following tables " + str(hive_table_list))
        return(hive_table_list)

    def dumpTablesHive(self,schemaname,col_to_ignore,custom_sleep= 60):
        table_list = []
        self.getCommandOutput("mkdir /data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname))
        table_list = self.returnTableListHive(schemaname)
        if table_list == []:
            self.logger.error("HIVE DB tables not found for schema " + schemaname + ", exiting the current flow")
            sys.exit(1)
        self.hive_dump_path = self.current_execution_folder + "/" + "HIVE_db_dump_" + str(schemaname)
        if not os.path.exists(self.hive_dump_path):
            os.makedirs(self.hive_dump_path)
        for table in table_list:
            dump_path = "/data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" +  str(table)
            self.getCommandOutput("mkdir " + dump_path,"#")
            command = "sudo -u hdfs hive -e \"insert overwrite local directory \'/tmp/" + table + "\' ROW FORMAT DELIMITED FIELDS TERMINATED BY \',\' select " + self.colListForTableHive(schemaname,table,col_to_ignore) + " from " + schemaname.strip() + "." + table + ";\""
            print command
            if table == "bin_metatable":
                command = "hive -e \"show partitions " + schemaname + "." + table + " ;\" > /data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" + table + "/" + str(table) + ".txt"
               #command =  "sudo -u hdfs hive -e \"insert overwrite local directory \'/tmp/" + table + "\' ROW FORMAT DELIMITED FIELDS TERMINATED BY \',\'show partitions " + schemaname.strip() + "." + table + ";\""
            #command = "hive -e \"select * from " + schemaname.strip() + "." + table + " ;\" > /data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" + str(table) + ".txt"
            self.getCommandOutput(command,"#")
            time.sleep(custom_sleep)
            self.getCommandOutput("cat /tmp/" + table + "/* >> " + dump_path + "/" + table + ".txt")
            time.sleep(10)
            self.scpReceiveFromServer("/data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" + table + "/" + table + ".txt",self.hive_dump_path,self.ipaddress,self.username,self.password)
            self.getCommandOutput("\n")
        time.sleep(custom_sleep)
        self.logger.info("Hive tables dumped at location: " + str(dump_path))
        self.hive_cleaup_path = "/data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname)

    def colListForTableHive(self,schemaname,table,col_to_ignore,custom_sleep=60):
        table_list = []
        self.getCommandOutput("mkdir /data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname))
        self.hive_dump_path = self.current_execution_folder + "/" + "HIVE_db_dump_" + str(schemaname)
        dump_path = "/data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" +  str(table)
        command = "hive -e \"describe " + schemaname + "." + table + " ;\" > /data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" + str(table) + "_schema.txt"
        self.getCommandOutput(command,"#")
        time.sleep(custom_sleep)     
        self.scpReceiveFromServer("/data/Test_Execution_Report/HIVE_db_dump_" + str(schemaname) + "/" + table + "_schema.txt",self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        time.sleep(2) 
        self.getCommandOutput("\n")
        f = open(self.tooldir + "/Tmp/" + table + "_schema.txt",'r')
        schema_text = f.readlines()
        f.close()
        ignore_col_list = []
        query_list = []
        if "," in col_to_ignore:
            ignore_col_list = col_to_ignore.split(",")
        else :
            ignore_col_list.append(col_to_ignore)
            
        ignore_col_list = map(lambda x:x.lower(),ignore_col_list)
        
        for line in schema_text:
            if line.strip() == "":
                break
            if line.split(" ")[0].strip().lower() not in ignore_col_list:
                query_list.append(line.split("\t")[0].strip().lower())

         
        print "Query after ignore" + str(query_list)
        self.logger.info("Columns for table " + str(table) + " : " + str(query_list))
        return(",".join(query_list))                          

 
    def getHostname(self):
        self.child.sendline("hostname")
        self.child.expect("#")
        return(self.child.before.splitlines()[1].strip())
        
    def createDir(self,directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def runJob(self,job_config_file,Jobname,epoch_time,schemaname,old_version,tc_title):
        application_id = ""
        self.getCommandOutput("mkdir /data/Test_Execution_Report/")
        job_path = "/data/Test_Execution_Report/" + Jobname + "_" + schemaname + "/"
        self.getCommandOutput("mkdir " + job_path)
        self.getCommandOutput("cd " + job_path)
        job_config_file = self.tooldir + "/" + "Config/" + job_config_file
        self.logger.info("Base Version: " + old_version)
        self.logger.info("Test Case Title: " + tc_title)
        f = open(job_config_file,'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            if line.startswith("job_command"):
                job_command = line.split("=")[1].strip()
            if line.startswith("job_config_file"):
                job_conf_file = line.split("=")[1].strip()
        #run_command = "\" sudo -u hdfs " +job_command + "\"" + " " + job_conf_file + " " + epoch_time + " >> " + job_path + "/" + "spark_execution.log"
        #sys.exit()
        self.job_nohup_path = job_path + "/nohup.out"
        self.job_path = job_path
        run_command = "nohup sudo -u hdfs " +job_command + " " + job_conf_file + " " + epoch_time + " &"
        print run_command
        self.getCommandOutput(run_command)
        self.getCommandOutput("\n")
        self.logger.info("Started Job: " + str(Jobname))
        time.sleep(200)
        self.scpReceiveFromServer(self.job_nohup_path,self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        f = open(self.tooldir + "/" + "Tmp/nohup.out",'r')
        app_id_list = f.readlines()
        for line in app_id_list:
            if "Application report for" in line:
                application_id = line.split("Application report for")[1].split("(")[0].strip()
                break
        self.application_id = application_id
        self.logger.info("Job Started with applicationID: " + self.application_id )
        if self.application_id == "":
            self.logger.error("Job failed to start as Application ID could not be found")
            sys.exit()
        else:
            return(0)
 
    def checkJobStatus(self):
        job_status_flag = "0"
        command_job_status = "yarn application -status " + self.application_id + " > /tmp/tmp_" + self.application_id + ".txt"
        self.getCommandOutput(command_job_status,"#")
        self.getCommandOutput("\n","#")
        time.sleep(5)
        self.scpReceiveFromServer("/tmp/tmp_" + self.application_id + ".txt",self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        f = open(self.tooldir + "/" + "Tmp/tmp_" +  self.application_id + ".txt",'r')
        lines = f.read()
        f.close()
        if "Final-State : SUCCEEDED" in lines and "State : FINISHED" in lines:
            job_status_flag = "SUCCESS"
            self.logger.info("success ::" + lines)
        if "Final-State : FAILED" in lines and "State : FINISHED" in lines:
            job_status_flag = "FAILED"
            self.logger.info("Failed " + lines)
        self.logger.info("Job Status for Application ID: " + self.application_id + " : " + job_status_flag)
        return(job_status_flag)
        print "Job Status for Application ID: " + self.application_id + " : " + job_status_flag

    def verifyJobCompletion(self,timeout = 30):
        for i in range(1,int(timeout)):
            job_completion_flag = self.checkJobStatus()
            time.sleep(60)
            if job_completion_flag != "0":
                break
            else:
                self.checkJobStatus()
        if job_completion_flag == "FAILED":
            self.logger.info("Scheduled job with applicationID " + self.application_id + " FAILED")
            sys.exit()
        self.scpReceiveFromServer(self.job_path,self.current_execution_folder,self.ipaddress,self.username,self.password)
        self.validateJobLogs()

    def configUpdateCare(self,filename,schema_name,input_location,scp_location):
        f = open(self.tooldir + "/" + "Config/" + filename,'r')
        output = f.readlines()
        f.close()
        self.deleteFile(self.tooldir + "/" + "Tmp/" + filename)
        for line in output:
            f = open(self.tooldir + "/" + "Tmp/" + filename,'a')
            if line.startswith("OUTPUT_DB_NAME") or line.startswith("INPUT_DB_NAME") or line.startswith("DB_NAME"):
                print line
                line = line.split("\t")[0] + "\t \t" + schema_name + "\n"
                print line
            if line.startswith("ROOT_DIR"):
                print line
                line = line.split("\t")[0] + "\t \t" + input_location + "\n"
                print line
            f.write(line)
        f.close()
        self.scpSendToSever(self.tooldir + "/" + "Tmp/" + filename,scp_location,self.ipaddress,self.username,self.password)
        for dn_ip in self.datanode_ip:
            self.scpSendToSever(self.tooldir + "/" + "Tmp/" + filename,scp_location,dn_ip,self.username,self.password)
    
        
    def validateJobLogs(self):
        self.scpReceiveFromServer(self.job_nohup_path,self.tooldir + "/" + "Tmp/",self.ipaddress,self.username,self.password)
        time.sleep(30)
        f = open(self.tooldir + "/" + "Tmp/nohup.out",'r')
        job_logs = f.readlines()
        for line in job_logs:
            if "xcep" in line or "error" in line:
                if "Address already in use" in line or "java.io.FileNotFoundException: derby.log" in line or "Failed to get database default, returning NoSuchObjectException" in line or "Will not attempt to authenticate using SASL" in line:
                    self.logger.error("Ignoring as it is a known exception " + line)
                else:
                    self.logger.error("Error/Exception trace seen: " + line)
 
    def diffTable(self,old_folder,db_type,custom_diff_path = ""):
        self.logger.info("Performing Diff between output of " + db_type)
        path_files = []
        new_files = []
        dict_old = {}
        dict_new = {}
        
        if db_type == "hive":
            new_files = os.listdir(self.hive_dump_path)
            new_folder = self.hive_dump_path
        if db_type == "impala":
            new_files = os.listdir(self.impala_dump_path)
            new_folder = self.impala_dump_path
        if db_type == "hbase":
            new_files = os.listdir(self.hbase_dump_path)
            new_folder = self.hbase_dump_path
        if "_" in db_type and "custom" in db_type:
            new_files = os.listdir(custom_diff_path)
            new_folder = custom_diff_path
            
            
        old_files = os.listdir(old_folder)

        diff_dict_counter = {}
        
        if "tables_file.txt" in old_files :
            old_files.remove("tables_file.txt")
        if "table_list.txt" in old_files :
            old_files.remove("table_list.txt")
        tmp_list = []
        for file in old_files:
            if "schema" not in file:
                tmp_list.append(file)
        old_files = tmp_list
                
            
        for file in old_files:
            
            match_count = 0
            mismatch_count_old = 0
            mismatch_count_new = 0
            duplicate_count = 0
            
            tmp_list_diff = []
            key_match_flag = "Passed"
            len_check_flag = "Passed"
                                                                   
            if os.path.isfile((new_folder + "/" + file).strip()) != True:
                self.logger.info("Stats for Diff Table " + db_type + " - Table : " + str(file) + " : File Not found in New DB")
                continue
            print old_folder + "/" + file

            print new_folder + "/" + file
            
            dict_old = self.createDictForDiff(old_folder + "/" + file)
            dict_new = self.createDictForDiff(new_folder + "/" + file)

            list_old = self.createLisForDiff(old_folder + "/" + file)
            list_new = self.createLisForDiff(new_folder + "/" + file)

            #1. Length check
            #print dict_new

            if len(list_old) == len(list_new):                
                len_check_flag = "Passed"
                self.logger.info("Length check Passed for: " + file)
            else:
                self.logger.info("Length check Failed for: " + file)
                self.logger.info("Row count Check:Failed , len old dump " + str(len(list_old)) + " len new dump " + str(len(list_new)))
                len_check_flag = "Failed"
        
            #2. Elements matching
            for key in dict_old:
                if key not in dict_new:
                    mismatch_count_old = mismatch_count_old + 1
                    self.logger.info("For File: " + file + " key match failed for key in old: " + str(key))
                    print "For File: " + file + "key match failed for key in old: " + str(key) 
                else:
                    match_count = match_count + 1
                                           
            for key in dict_new:
                if key not in dict_old:
                    mismatch_count_new = mismatch_count_new + 1
                    self.logger.info("For File: " + file + "key match failed for key in new: " + str(key))
                    print "For File: " + file + "key match failed for key in new: " + str(key)

            for key in dict_old:
                if key in dict_new:
                    if dict_old[key] != dict_new[key]:
                        self.logger.info("Duplicate Check failed for key: " + str(key))
                        duplicate_count = duplicate_count + 1
                        
                    

            for key in dict_new:
                if key in dict_old:
                    if dict_new[key] != dict_old[key]:
                        self.logger.info("Duplicate Check failed for key: " + str(key))
                        duplicate_count = duplicate_count + 1

            tmp_list_diff.append("match_count = " + str(match_count))
            tmp_list_diff.append("mismatch_count_old = " + str(mismatch_count_old))
            tmp_list_diff.append("mismatch_count_new = " + str(mismatch_count_new))
            tmp_list_diff.append("duplicate_count = " + str(duplicate_count))
            diff_dict_counter[file] = tmp_list_diff
            print diff_dict_counter
        for (k,v) in diff_dict_counter.items():
            print "Stats for Diff - Table : "  + str(k) + " diff result " + str(v)
            self.logger.info("Stats for Diff - Table :" + db_type  +   " - Table :" + str(k) + " diff result: " + str(v))

    def createLisForDiff(self,filename):
        return_list = []
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            return_list.append(line)
        return(return_list) 
        
                    
    def createDictForDiff(self,filename):
        return_dict = {}
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            if line not in return_dict:
                return_dict[line] = 1
            else:
                return_dict[line] = return_dict[line] + 1
        return(return_dict) 

    def deleteFile(self,filename):
        if os.path.exists(filename):
            os.remove(filename)


    def cleanup(self):
        
        if self.hive_cleaup_path != None:
            self.getCommandOutput("cd /tmp/")
            self.getCommandOutput("rm -rf " + self.hive_cleaup_path)

        if self.hbase_cleaup_path != None:
            self.getCommandOutput("cd /tmp/")
            self.getCommandOutput("rm -rf " + self.hbase_cleaup_path)

        if self.impala_cleaup_path!= None:
            self.getCommandOutput("cd /tmp/")
            self.getCommandOutput("rm -rf " + self.impala_cleaup_path)

        if self.job_path != None:
            self.getCommandOutput("cd /tmp/")
            self.getCommandOutput("rm -rf " + self.job_path)
        

## Unit Test Cases


#test_obj_run = RegressionModule()
#test_obj_run.connectToMachine("root","root@123","192.168.113.188")
#test_obj_run.getDnIpaddress()


#test_obj_run.connectToMachine("root","root@123","192.168.194.166")
#test_obj_run.returnTableListImpala("agg_p5")
#test_obj_run.dumpTablesImpala("agg_p5")
#test_obj_run.returnTableListPhoenix("TEST1")
#test_obj_run.returnTableListHive("monthly_test")
#test_obj_run.configUpdateCare("care_ldm_properties.ini","test_v1","/cdr_bz2_off_dir/cdr_bz2_off","/opt/reflex/opt/care/ldm/cdr")
#test_obj_run.runJob("care_ldm_job_config","CDR_LDM_JOB","1475824500","test_v1")
#test_obj_run.checkJobStatus()

