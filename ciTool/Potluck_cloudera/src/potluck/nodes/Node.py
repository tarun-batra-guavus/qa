"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides the base methods to be used with node handles

Most of the methods are used internally by the framework.
View Source to take a look at all the methods.
"""

import pexpect
import sys
import re
import time
import commands
import os
import datetime
from potluck.logging import logger
from potluck.reporting import report
from potluck.nodes import CLI_MODES
from potluck import utils
from settings import REMOTE_DIR, ROOT_DIR
import threading
import shutil
globalCount = 0
ansi_escape_chars = re.compile(r'(?m)((\x1b[^m\r\n]*m)|(\x1b[^\r\n]+\x1b[=>]))')
def remove_special(s):
    """Removes special characters (mostly ANSI) seen in command outputs, from gingko platform onwards"""
    return ansi_escape_chars.sub('', s)
class Node(object):
    """Base class for all type of Nodes. Specific node types (like NN, DN etc.)
    are inherited from this class

    Default values associated with all nodes are:

    * Username: admin
    * Connection type: ssh
    * Connection port: 22
    """

    def __init__(self, node):
        """
        constructor to initialize various parameters IP and Port of a node. This can be overridden
        in the derived classes if the nodes use some non-default parameters
        like connection type, port number, username

        `node` should be dict with the below format::

            {
                'alias': 'UI1',
                'type': 'NameNode',
                'connection': 'ssh',
                'ip': '192.168.154.7',
                'port': '22'
                'password': 'root@123',
            }
        """
        # _session will hold the underlying pexpect session handle
        self._session = None
        self.alias = node["alias"]
        self.ip = node["ip"]
        self.password = node["password"]
        self.port = node["port"]
        self.connection_type = node["connection"]
        self.info = node    # Store the raw testbed information
        self.promptuser = r"[\r\n][^\r\n]* # "
        self.promptshell = r"\[(root|admin)\@[\.a-zA-Z0-9-]+ [\~]+\]\# "
	
        self.prompts = {
            "user"   : re.compile(self.promptuser),
            CLI_MODES.shell  : re.compile(self.promptshell),
        }
        self.promptmore = re.compile(r"lines \d+-\d+")
        self._mode = None
        self._mode_stack = []
        self.connect()

    def __str__(self):
        return "%s <%s>" % (self.alias, self.ip)

    def __remote_id__(self):
        """Returns the ID of the object to be used for remoting testcases"""
        return hash(self)

    def __getattr__(self, name):
        try:
            # Provides access to the members of node info dict
            return getattr(self.info, name)
        except AttributeError:
            raise AttributeError("Parameter '%s' is not present in node '%s'" % (name, self.alias))



    def grepVersion(self,processname, version):
        logger.info("Monitoring of process %s" % processname)
        # Connect to the device and get a node object
        logger.info("Checking the version for %s process" % processname)
        self.setMode("shell")
        output = self.sendCmd("rpm -qa | grep  -i " + '"' + processname + '"' + " | grep " + '"' + version + '"')
        if len(re.findall(r"%s" % processname, output, re.IGNORECASE)) > 0:
            return (1)
        else:
            return (0)

    def grepVersionbyCommand(self, processname, command, version):
        logger.info("Monitoring of process %s" % processname)
        # Connect to the device and get a node object
        logger.info("Checking the version for %s process" % processname)
        self.setMode("shell")
        output = self.sendCmd("%s"%command)
        if len(re.findall(r"%s" % version, output, re.IGNORECASE)) > 0:
            return (1)
        else:
            return (0)


    def grepDockerVersions(self,processname, version):
        logger.info("Monitoring of Docker process %s" % processname)
        # Connect to the device and get a node object
        logger.info("Checking the version for %s process" % processname)
        self.setMode("shell")
        output = self.sendCmd("docker images | grep -i " + '"' + processname + '"' + "| awk -F " + '"' + " " + '"' + " '{print $2}'")
        vers = version.split("\r")
        out = output.split("\r")
        if out[0] == vers[0]:
            return (1)
        else:
            return (0)

    def systemctlProcess(self, processname):
        logger.info("Monitoring of %s process"%processname)
        # Connect to the device and get a node object
        logger.info("Checking that %s process is running"%processname)
        self.setMode("shell")
        output = self.sendCmd("systemctl status %s | grep -i \"running\" " %(processname))
        if len(output) > 0:
            return (1)
        else:
            return (0)

### dockerProcess sub-routine is being used for checking Docker's sub processes ###

    def dockerProcess(self, processname):
        logger.info("Monitoring of %s process"%processname)
        # Connect to the device and get a node object
        logger.info("Checking that %s process is running"%processname)
        self.setMode("shell")
        output = self.sendCmd("docker ps  | grep -i \"%s\""%processname)
        if len(output) > 0:
            return (1)
        else:
            return (0)


    def kafkaBrokers(self, ipaddr):
        broker_list = []
        logger.info("Counting Number of Kafka Brokers")
        # Connect to the device and get a node object
        self.setMode("shell")
        broker_list = self.sendCmd("echo \"ls /brokers/ids\" | zookeeper-shell %s:2181 | tail -1 | awk '{n=split($0,array,\",\")} END {print n}'"%ipaddr)
        output = broker_list.split("\n")
        return output[0]


    def fileExist(self, file):
        logger.info("Monitoring of File %s" % file)
        # Connect to the device and get a node object
        logger.info("Checking that %s exist's" %(file))
        output = self.sendCmd("ls -lrt %s"%(file))
        if len(re.findall(r"%s" % file, output, re.IGNORECASE)) > 0:
                return (1)
        else:
                return (0)


    def reboot(self):
        """Reboots the machine, and waits till it comes back up"""
        self.resetStream()
        logger.info("Going to reboot %s" % self)
        self.setMode(CLI_MODES.shell)
        self._session.sendline("reboot")
        reboot_failed_tries = 3
        reboot_wait_tries = 3
        while True:
            i = self._session.expect([
                            "The system is going down for reboot",
                            "System shutdown initiated",
                            "Connection to [\.\d]* closed",
                            pexpect.EOF,
                            "Request failed",
                            pexpect.TIMEOUT,
                            ], timeout=120)
            if i == 0 or i == 1:
                logger.info("Reboot initiated")
                continue
            elif i == 2 or i == 3:
                logger.info("Machine Rebooted. Connection closed")
                break
            elif i == 4:
                if reboot_failed_tries > 0:
                    logger.info("Reboot failed. Trying again...")
                    self._session.sendline("reload force")
                    reboot_failed_tries -= 1
                    continue
            elif i == 5:
                if reboot_wait_tries > 0:
                    logger.warn("Waited for 120 secs, but machine did NOT reboot. Waiting for sometime more...")
                    self._session.sendline("reload force")
                    reboot_wait_tries -= 1
                    continue
                else:
                    logger.error("Machine did NOT reboot!!!")
                    return False
            # break to prevent infinite loop
            break

        self._session.logfile_read.flush()
        self._session.logfile_read = None
        sys.stdout.flush()
        self.disconnect()
        logger.debug("Waiting for 300secs..")

        time.sleep(300)
        return self.waitTillReachable(180, timeout=1800)



    def waitTillReachable(self, sleep_per_try_secs=120, timeout=1200):
        """Keeps pinging the node until it is reachable or timeout occurs."""
        elapsed_time = 0
        while elapsed_time < timeout:
            if self.isReachable():
                logger.info("Machine pingable. Reconnecting after 30 secs..")
                time.sleep(30)
                self.connect()
                return True
            else:
                logger.info("Machine not yet pingable. Waiting for %s secs before retrying.." % sleep_per_try_secs)
                time.sleep(sleep_per_try_secs)
            elapsed_time += sleep_per_try_secs
        logger.warning("TIMEOUT: Waited for %d secs, but machine still not reachable" % elapsed_time)
        return False

    def isReachable(self):
        """Pings the node and check if it is reachable"""
        cmd = "ping -c 1 %s" % self.ip
        ping_output = commands.getoutput(cmd)
        logger.debug(cmd)
        logger.debug(ping_output)
        return re.search("1[\s\w]+received", ping_output) is not None



    def download_rpm(self,summary_handle,length,imageurl_final,role):
        cmd1 = "wget -A rpm -nd -r -np -nH --cut-dirs=%s --auth-no-challenge -e robots=off --reject 'index.html*' %s" %(length,imageurl_final)  
        self.sendCmd(cmd1,300)
        summary_handle.write("wget,%s,%s,pass \n" %(self,role))





    def listDirectory(self, directory):
        """Returns the list of contents of a directory

        :param directory: The path of the directory to be listed
        :returns: List of dict in the format {"filename" : filename, "type" : filetype}
        """
        self.pushMode(CLI_MODES.shell)
        output = self.sendCmd("ls -F %s" % directory)
        self.popMode()
        if "No such file" in output:
            return []
        output_list = []
        for filename in output.split():
             output_list.append(filename)
        return output_list





    def upgrade(self,summary_handle,role,rpm_keyword,image_url,dir_installer,exit_flag,mode,summary_var_dict={}):
        """Method to upgrade the image"""
        if image_url.endswith("/"):
            imageurl_final = image_url
        else:
            imageurl_final = image_url + "/"

        length = len(imageurl_final.split('/')) -4
        cmd = "yum clean all"
        self.sendCmd(cmd,300)
        dir_installer_role = dir_installer + "/" + role
        self.changeDirectory(dir_installer_role)
        tmp_var = "wget%s%s" %(self,role)

        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "false":
                self.download_rpm(summary_handle,length,imageurl_final,role)
        else:
            self.download_rpm(summary_handle,length,imageurl_final,role)


        num_files = "ls -lrt *\.rpm  | grep %s-[0-9]  | awk \'{print $NF}\' | xargs ls -t | tail -n1" %rpm_keyword
        output = self.sendCmd(num_files).split("\n")
        for each in output:
           if each.rstrip().endswith("rpm"):

               ##### Step added for uninstalling the rpm before installing 
               tmpcmd = "yum -y remove " + each.rstrip().rstrip(".rpm")


               tmpcmd1 = "yum -y install " + each.rstrip()
               tmp_var = "%s%s%s" %(tmpcmd1,self,role)

               ##### IF loop added for recovery option
               if mode == "RECOVERY":
                   flag = self.check_var_in_dict(tmp_var,summary_var_dict)
                   if flag == "true":
                       continue


               output = self.sendCmd(tmpcmd,600)
               output = self.sendCmd(tmpcmd1,600)
               time.sleep(30)
               output1 = self.sendCmd("echo $?").split("\n")
               output2 = [item.replace("\r", "") for item in output1]
               if "0" not in output2 :
                   summary_handle.write("%s,%s,%s,fail \n" %(tmpcmd1,self,role))
                   if exit_flag == "yes":
                       report.fail("Installation failed for %s on node %s having role %s with following error message : \n %s" %(each.strip(),self,role,output))
                   else:
                       logger.info("Installation failed for %s on node %s having role %s with following error message : \n %s" %(each.strip(),self,role,output))
               else:
                   summary_handle.write("%s,%s,%s,pass \n" %(tmpcmd1,self,role))
                   logger.info("Successful installation of %s on node %s having role %s" %(each.strip(),self,role))



    def stop_process(self,summary_handle,role,process_name,process_command,exit_flag,mode,summary_var_dict={}):
        output1 = []
        tmp_var = "%s%s%s%s" %(process_name,process_command,self,role)

        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return


        self.setMode("shell")
        #logger.info ("Stopping the process %s on node %s with role %s using command %s"  %(process_name,self,role,process_command))
        output = self.sendCmd(process_command)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" not in output2 :
            summary_handle.write("%s,%s,%s,%s,fail \n" %(process_name,process_command,self,role))
            if exit_flag == "yes":
                report.fail ("Stopping the process failed for %s on node %s having role %s with following error message : \n %s" %(process_name,self,role,output))
            else:
                logger.info("Stopping the process failed for %s on node %s having role %s with following error message : \n %s" %(process_name,self,role,output))
        else:
            summary_handle.write("%s,%s,%s,%s,pass \n" %(process_name,process_command,self,role))
            logger.info ("Successfully Stopped the process %s on node %s with role %s using command %s"  %(process_name,self,role,process_command))




    def backup_create_repos(self,summary_handle,role,image_url,mode,summary_var_dict={}):
        output1 = []
        filelist = []
        if image_url.endswith("/"):
            imageurl_final = image_url
        else:
            imageurl_final = image_url + "/"
        tmp_var = "repos%s%s" %(self,role)
 
        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return
    
        dir = "/etc/yum.repos.d"
        dir_backup = dir + "_backup_ci_tool"


        tmp_file = "useroutput/ci_tool.repo"
        f_in = open(tmp_file, "w")
        f_in.write("[mrx]\n")
        f_in.write("baseurl = %s\n" %imageurl_final)
        f_in.write("enabled = 1\n")
        f_in.write("gpgcheck = 0\n")
        f_in.write("name = MRX Repo\n")
        f_in.close()


        filelist = self.listDirectory(dir_backup)
        if filelist:
            self.copyFromLocal(tmp_file, dir)
            return 
        backup_cmd = "mv %s %s" %(dir,dir_backup)
        output = self.sendCmd(backup_cmd)         
        create_cmd = "mkdir -p %s" %dir
        output = self.sendCmd(create_cmd)
        self.copyFromLocal(tmp_file, dir)
        summary_handle.write("repos,%s,%s,pass \n" %(self,role))



    def restore_repos(self,summary_handle,role,mode,summary_var_dict={}):
        output1 = []
        
        tmp_var = "repos_backup%s%s" %(self,role)

        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return
   
        dir = "/etc/yum.repos.d"
        dir_backup = dir + "_backup_ci_tool"
        remove_cmd = "rm -rf %s" %dir
        output = self.sendCmd(remove_cmd)
        restore_cmd = "mv %s %s" %(dir_backup,dir)
        output = self.sendCmd(restore_cmd)
        summary_handle.write("repos_backup,%s,%s,pass \n" %(self,role))


    def getCommandOutput(self,command,expect = "#",sleepTime = "5"):
        #expect = r"\[root\@[\.a-zA-Z0-9]+ [\~]+\]\#"
        #print "Running command: " + command
        self.child.sendline(command)
        time.sleep(int(sleepTime))
        self.child.expect(expect)
        logger.info("Running command : " + command)
        print self.child.before
        return(self.child.before)



    def runJobAzkaCli(self,summary_handle,project_name,running_jobs_name,role,mode,summary_var_dict={}):
        exec_flag  = 0
        for job in reversed(running_jobs_name):


            tmp_var = "start%s%s%s" %(job,self,role)
        ##### IF loop added for recovery option
            if mode == "RECOVERY":
                flag = self.check_var_in_dict(tmp_var,summary_var_dict)
                if flag == "true":
                    continue

            command = "azkacli flow submit %s %s" %(project_name,job)
            logger.info ("Command to run the job is %s" %command)
            output = self.sendCmd(command)
            if "exec id" in output:
                logger.info("Projectname : %s jobname : %s successfully submitted to azkacli" %(project_name,job))
                summary_handle.write("start,%s,%s,%s,pass \n" %(job,self,role))
            else:
                logger.info("Projectname : %s jobname : %s exec id not found" %(project_name,job))
                summary_handle.write("start,%s,%s,%s,fail \n" %(job,self,role))
                

    def checkAzkaMaster(self,port = "8888"):
        command = "curl -k -X POST --data \"action=login&username=azkaban&password=azkaban\" http://" + self.ip + ":" + str(port)
        output = self.sendCmd(command)
        print output
        if "success" in output:
            return "true"
        else:
            return "false"

    def grepAzkabanCli(self):
        logger.info("Monitoring of Azkaban CLI")
        # Connect to the device and get a node object
        logger.info("Checking that Azkaban CLI is accessible")
        self.setMode("shell")
        output = self.sendCmd("azkacli healthcheck | grep -i \"OK\" | grep -v grep")
        if len(output) > 0:
            return (1)
        else:
            return (0)

    def azkabanRestAPI(self, ipaddr, port):
        logger.info("Monitoring of Azkaban REST APIs")
        # Connect to the device and get a node object
        logger.info("Checking that Azkaban REST APIs is accessible")
        self.setMode("shell")
        output = self.sendCmd("curl -k -X POST --data \"action=login&username=azkaban&password=azkaban\" http://%s:%s |grep -i \"SUCCESS\""%(ipaddr,port))
        if len(output) > 0:
            return (1)
        else:
            return (0)

    def systemd_linked_process_HA(self, process_list , time_to_restart = 300):
        logger.info("Monitoring of list of Systemd Linked processes : %s" % process_list)
        flag = 1
        # Connect to the device and get a node object
        for process in process_list:
            logger.info("Checking that %s process is running" % process)
            output = self.systemctlProcess(process)
            pid = self.sendCmd("systemctl status %s | grep -i \"Main PID:\" | awk -F \" \" '{print $3}'"%process).split('\r\n')
            if output == 1:
                logger.info("%s Process is running"%process)
                logger.info("Killing %s Process"%process)
                self.sendCmd("kill -9 %s"%pid[0])
            else:
                logger.info("%s Process is not running"%process)
        sleep(float(time_to_restart))
        for process in process_list:
            logger.info("Checking that %s process is running after killing" % process)
            output = self.systemctlProcess(process)
            pid = self.sendCmd("systemctl status %s | grep -i \"Main PID:\" | awk -F \" \" '{print $3}'"%process).split('\r\n')
            if output == 1:
                logger.info("%s Process is running After Killing"%process)
            else:
                logger.info("%s Process is not running running after killing"%process)
                flag = 0
        if flag == 1:
            return (1)
        else:
            return(0)




    def getRunningJobId(self,projectName):
        runJobList = []
        command = "azkacli executions running |  sed -r \"s/\\x1B\\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g\" "
        logger.info ("Command to check the running jobs is %s" %command)
        output = self.sendCmd(command)
        if "There are no flow" in output:
            runJobList = []
        else:
            for line in output.split("\n"):
                if projectName.lower() in line.lower():
                    
                    runJobList.append(line.split()[0].strip())
                    runJobList.append(line.split()[2].strip())
        return runJobList


    def stopRunningJobs(self,summary_handle,role,runJobList,running_jobs_name,mode,summary_var_dict={}):
        port = "8888"
        i = 0
        for id in runJobList:
            tmp_var = "stop%s%s%s" %(running_jobs_name[i],self,role)
        ##### IF loop added for recovery option
            if mode == "RECOVERY":
                flag = self.check_var_in_dict(tmp_var,summary_var_dict)
                if flag == "true":
                    i+=1
                    continue



            print "curl -k --get --data \"session.id=`curl -k -X POST --data \"action=login&username=azkaban&password=azkaban\" http://" + self.ip + ":" + str(port) + " |grep \"session.id\" |cut -d\'\"\' -f4`&ajax=cancelFlow&execid=" + str(id) + "\""  + " http://" +   self.ip + ":" + str(port) + "/executor"
            self.sendCmd("curl -k --get --data \"session.id=`curl -k -X POST --data \"action=login&username=azkaban&password=azkaban\" http://" + self.ip + ":" + str(port) + " |grep \"session.id\" |cut -d\'\"\' -f4`&ajax=cancelFlow&execid=" + str(id) + "\"" +  " http://" +  self.ip + ":" + str(port) + "/executor")


            output1 = self.sendCmd("echo $?").split("\n")
            output2 = [item.replace("\r", "") for item in output1]
            if "0" not in output2 :
                summary_handle.write("stop,%s,%s,%s,fail \n" %(running_jobs_name[i],self,role))
            else:
                summary_handle.write("stop,%s,%s,%s,pass \n" %(running_jobs_name[i],self,role))
                logger.info ("Successfully Stopped the jobs %s on node %s with role %s "  %(running_jobs_name[i],self,role))
            i+=1

        








    def start_process(self,summary_handle,role,process_name,process_command,exit_flag,mode,summary_var_dict={}):
        output1 = []
        tmp_var = "%s%s%s%s" %(process_name,process_command,self,role)

        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return


        self.setMode("shell")
        #logger.info ("Starting the process %s on node %s with role %s using command %s"  %(process_name,self,role,process_command))
        output = self.sendCmd(process_command)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" not in output2  :
            summary_handle.write("%s,%s,%s,%s,fail \n" %(process_name,process_command,self,role))
            if exit_flag == "yes":
                report.fail ("Starting the process failed for %s on node %s having role %s with following error message : \n %s" %(process_name,self,role,output))
            else:
                logger.info("Starting the process failed for %s on node %s having role %s with following error message : \n %s" %(process_name,self,role,output))
        else:
            summary_handle.write("%s,%s,%s,%s,pass \n" %(process_name,process_command,self,role))
            logger.info ("Successfully Started the process %s on node %s with role %s using command %s"  %(process_name,self,role,process_command))



    def stop_job(self,summary_handle,role,listpassed,mode,summary_var_dict={}):
        i = 0
        output1 = []
        while i < len(listpassed):
            tmp_var = "%s%s%s%s" %(listpassed[i],listpassed[i+1],self,role)

            ##### IF loop added for recovery option
            if mode == "RECOVERY":
                flag = self.check_var_in_dict(tmp_var,summary_var_dict)
                if flag == "true":
                    i+=3
                    continue

            self.setMode("shell")
            #logger.info ("Stopping the jobs %s on node %s with role %s using command %s"  %(listpassed[i],self,role,listpassed[i+1]))
            output = self.sendCmd(listpassed[i+1],300)
            output1 = self.sendCmd("echo $?").split("\n")
            output2 = [item.replace("\r", "") for item in output1]
            if "0" not in output2 :
                summary_handle.write("%s,%s,%s,%s,fail \n" %(listpassed[i],listpassed[i+1],self,role))
                if listpassed[i+2] == "yes":
                    report.fail ("Stopping the jobs failed for %s on node %s having role %s with following error message %s"  %(listpassed[i],self,role,output))
                else:
                    logger.info ("Stopping the jobs failed for %s on node %s having role %s with following error message %s"  %(listpassed[i],self,role,output))
            else:
                summary_handle.write("%s,%s,%s,%s,pass \n" %(listpassed[i],listpassed[i+1],self,role))
                logger.info ("Successfully Stopped the jobs %s on node %s with role %s using command %s"  %(listpassed[i],self,role,listpassed[i+1]))
            i+=3


    def apply_mop(self,summary_handle,role,mop_command,exit_flag,mode,summary_var_dict={}):
        output1 = []
        tmp_var = "%s%s%s" %(mop_command,self,role)

        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return
 

        self.setMode("shell")
        #logger.info ("Applying MOP %s on node %s with role %s "  %(mop_command,self,role))
        output = self.sendCmd(mop_command)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" not in output2 :
            summary_handle.write("%s,%s,%s,fail \n" %(mop_command,self,role))
            if exit_flag == "yes":
                report.fail ("Applying MOP  %s on node %s having role %s failed with following error message %s"  %(mop_command,self,role,output))
            else:
                logger.info ("Applying MOP  %s on node %s having role %s failed with following error message %s"  %(mop_command,self,role,output))
        else:
            summary_handle.write("%s,%s,%s,fail \n" %(mop_command,self,role))
            logger.info ("Successfully applied MOP  %s on node %s having role %s "  %(mop_command,self,role))




    def files_backup(self,summary_handle,role,listpassed,dir_backup,mode,summary_var_dict={}):
        i = 0
        output1 = []
        tmpList = []
        dir_backup_role = dir_backup + "/" + role
        while i < len(listpassed):
            tmp_var = "%s%s%s" %(listpassed[i+2],self,role)

            ##### IF loop added for recovery option
            if mode == "RECOVERY":
                flag = self.check_var_in_dict(tmp_var,summary_var_dict)
                if flag == "true":
                    i+=4
                    continue


            self.setMode("shell")
            #logger.info ("Taking file backup on node %s with role %s for file %s"  %(self,role,listpassed[i+2]))

            tmp_var1 = listpassed[i+2].replace("/",":")
            file_name = tmp_var1.lstrip(":")

            cmd3 = "cp %s %s/%s" %(listpassed[i+2],dir_backup_role,file_name)

            output = self.sendCmd(cmd3)
            output1 = self.sendCmd("echo $?").split("\n")
            output2 = [item.replace("\r", "") for item in output1]
            if "0" not in output2 :
                summary_handle.write("%s,%s,%s,fail \n" %(listpassed[i+2],self,role))
                summary_handle.write("File backup on node %s with role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
                if listpassed[i+3] == "yes":
                    report.fail ("File backup on node %s with role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
                else:
                    logger.info ("File backup on node %s with role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
            else:
                summary_handle.write("%s,%s,%s,pass \n" %(listpassed[i+2],self,role))
                logger.info ("Successful file backup taken on node %s with role %s for file %s"  %(self,role,listpassed[i+2]))
            i+=4






    def copy_backup_files(self,summary_handle,role,listpassed,dir_backup,dir_build_content,mode,summary_var_dict={}):
        i = 0
        output1 = []
        dir_role = dir_backup + "/" + role
        dir_build_content_role = dir_build_content + "/" + role
        while i < len(listpassed):
             tmp_var1 = listpassed[i+2].replace("/",":")
             file_name = tmp_var1.lstrip(":")
             backup_file_path = dir_role + "/" + file_name
             tmp_var = "%s%s%s" %(backup_file_path,self,role)


             ##### IF loop added for recovery option
             if mode == "RECOVERY":
                 flag = self.check_var_in_dict(tmp_var,summary_var_dict)
                 if flag == "true":
                     i+=4
                     continue



             cmd1 = "cp %s %s/%s" %(listpassed[i+2],dir_build_content_role,file_name)
             output = self.sendCmd(cmd1)
             output1 = self.sendCmd("echo $?").split("\n")
             output2 = [item.replace("\r", "") for item in output1]
             if "0" not in output2 :
                 if listpassed[i+3] == "yes":
                     report.fail ("Build File backup on node %s having role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
                 else:
                     logger.info ("Build File backup on node %s having role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
             else:
                 logger.info ("Successful Build File backup taken on node %s having role %s for file %s "  %(self,role,listpassed[i+2]))


             cmd2 = "scp %s %s" %(backup_file_path,listpassed[i+2])
             output = self.sendCmd(cmd2)
             output1 = self.sendCmd("echo $?").split("\n")
             output2 = [item.replace("\r", "") for item in output1]
             if "0" not in output2 :
                 summary_handle.write("%s,%s,%s,fail \n" %(backup_file_path,self,role))
                 if listpassed[i+3] == "yes":
                     report.fail ("Copying operation from  backup file location %s to build file location %s on node %s having role %s failed with following error %s "  %(backup_file_path,listpassed[i+2],self,role,output))
                 else:
                     logger.info ("Copying operation from  backup file location %s to build file location %s on node %s having role %s failed with following error %s "  %(backup_file_path,listpassed[i+2],self,role,output))
             else:
                 summary_handle.write("%s,%s,%s,pass \n" %(backup_file_path,self,role))
                 logger.info ("Copying operation from  backup file location %s to build file location %s on node %s having role %s is successful"  %(backup_file_path,listpassed[i+2],self,role))
             i+=4



    def check_var_in_dict(self,key1,dict1):
        if key1 in dict1.keys():
            if dict1[key1].upper() == "PASS":
                return "true"
        return "false"
        

    def check_process(self,summary_handle,each,processname,mode,summary_var_dict={}):
        logger.info("Monitoring of process %s" % processname)
        tmp_var = "%s%s%s" %(processname,self,each)

        ##### IF loop added for recovery option
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return
 

        self.setMode("shell")
        cmd = "ps -ef | grep -i %s | grep -v grep" %(processname)
        output = self.sendCmd(cmd)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" in output2 :
            report.fail("Following yum process :%s running on node %s with role %s" %(output,self,each))
        else:
            summary_handle.write("%s,%s,%s,pass \n" %(processname,self,each))
            logger.info ("No yum process running on node")




    def connect(self):
        """Internally used by Potluck to connect to the node, by taking care of the connection type used.

        For now, only ssh connections are supported
        """
        if self.connection_type == "ssh":
            self._session = self.connectSsh()
        else:
            raise NotImplementedError("Connection type not implemented: %s" % connection_type)

    def disconnect(self):
        self._session.close()

    def isConnected(self):
        """Returns True is the node is connected, otherwise returns False"""
        if self._session is None:
            return False
        return self._session.isalive() is True

    def reconnect(self):
        current_mode = self.getMode()
        self.disconnect()
        self.connect()
        # Switch back to the mode that we were already in
        self.setMode(current_mode)



    def connectSsh(self):
        """__
        Connects to the node using ssh and returns the session handle
        """
        connect_handle = pexpect.spawn("ssh -q -o StrictHostKeyChecking=no root@%s" % self.ip)
        connect_handle.setwinsize(800,800)
        connect_handle.logfile_read = sys.stdout
        #connect_handle.logfile_send = sys.stdout
        i = 0
        ssh_newkey = r'(?i)Are you sure you want to continue connecting'
        remote_key_changed = r"REMOTE HOST IDENTIFICATION HAS CHANGED"

        perm_denied = r"(?i)Permission denied"
        while True:
            i = connect_handle.expect([ssh_newkey, 'assword:',self.promptshell,
                                        pexpect.EOF, pexpect.TIMEOUT,
                                        remote_key_changed, perm_denied])
            if i==0:
                connect_handle.sendline('yes')
                continue
            elif i==1:
                 logger.info("Password supplied")
                 connect_handle.sendline(self.password)
                 continue
	    elif i==2:
                self._mode = CLI_MODES.shell
                self._prompt = self.promptshell
                break
            elif i==3:
                logger.info("Connection closed: %s" % self)
                logger.info(connect_handle.before) # print out the result
                raise ValueError("Connection Closed: %s" % self)
            elif i==4:
                logger.warning("Timeout while waiting for connection")
                logger.info(connect_handle.before) # print out the result
                raise ValueError("Unable to establish connection %s" % self)
            elif i==5:
                logger.warn("Removing offending key from .known_hosts..")
                known_hosts_file = os.path.expanduser("~/.ssh/known_hosts")

                if "darwin" in sys.platform.lower():
                    # MAC OS
                    utils.run_cmd("sed -i 1 's/%s.*//' %s" % (self.ip, known_hosts_file))
                elif "linux" in sys.platform.lower():
                    # Linux
                    utils.run_cmd("sed -i 's/%s.*//' %s" % (self.ip, known_hosts_file))

                connect_handle = pexpect.spawn("ssh root@%s" % self.ip)
                connect_handle.setwinsize(800,800)
                connect_handle.logfile_read = sys.stdout

                continue
            elif i==6:
                logger.warning("Permission denied: %s" % self)
                logger.info(connect_handle.before) # print out the result
                raise ValueError("Permission denied: %s." % self)
        return connect_handle

    def resetStream(self, stream=None):
        # Stream should be reset everytime, otherwise cleanup action's log won't be printed in any other file
        if stream is None:
            self._session.logfile_read = sys.stdout
        else:
            self._session.logfile_read = stream

    def initShell(self):
        self.sendCmd("unalias cp ls")


    def run_cmd(self,command,custom_expect = '#',timeout=30,ignoreErrors=False):
        #custom_expect = '#'
        print "command: %s" %command
        try:
            available_data = self._session.read_nonblocking(size=1000, timeout=0.5)   # Read all available output
            if re.search("logging out", available_data, flags=re.I):
                logger.info("Logged out due to inactivity. Reconnecting..")
                self.reconnect()
        except pexpect.TIMEOUT: pass
        self.last_output = ""
        self._session.sendline(command)
        i = self._session.expect([pexpect.EOF, pexpect.TIMEOUT, "logging out" ,self.promptmore,custom_expect],timeout=timeout)
        if i == 0:
                # EOF
                logger.error("Connection closed %s" % self)
                raise ValueError("Connection Closed")
        elif i == 1:
                # TIMEOUT
                logger.error(str(self._session))
                logger.error("Time Out")
                raise ValueError("Time Out")
        elif i == 2:
                logger.info("Logged out due to inactivity. Reconnecting..")
                self.reconnect()
                self._session.sendline(cmd)
        elif i == 3:
                # More prompt. Send Space
                self.last_output += self._session.before
                self._session.send(" ")
        elif i == 4:
                self.last_output += self._session.before
                logger.info("executed command successfully")
        self.last_output = re.sub("(?m)" + re.escape(command), "", self.last_output)
	if not ignoreErrors and re.search("\b:*(error|unable|failed|failure|unrecognized command):*\b", self.last_output, re.I):
            logger.error("Error while executing command")

        if command.startswith("hadoop"):
            self.last_output = re.sub(r"(?m)^\s*WARNING:.*$", "", self.last_output)

        # Remove some special characters seen in new platforms (gingko onwards)
        ret_val = remove_special(self.last_output)
        return ret_val.strip()
    def getCommandOutput(self,command,expect = "#"):
        print "Running command: " + command
        self._session.sendline(command)
        self._session.expect(expect)
	self.last_output = self._session.before
        return(self.last_output)

    def sendCmd(self, cmd, timeout=300, ignoreErrors=False,expected_param = "]#"):
        """Sends a command to node and returns the output of the command

        :param cmd: Command to send to the node
        :param timeout: Time to wait for the command to complete
        :param ignoreErrors: If ignoreErrors is False, any error in the
                             command output will be logged as logger.error
        """
        self.resetStream()

        cmd = cmd.strip()
        cmd = re.sub(r"[\r\n\t\s]+", " ", cmd)
        try:
            available_data = self._session.read_nonblocking(size=1000, timeout=0.5)   # Read all available output
            if re.search("logging out", available_data, flags=re.I):
                logger.info("Logged out due to inactivity. Reconnecting..")
                self.reconnect()
        except pexpect.TIMEOUT: pass

        self._session.sendline(cmd)

        self.last_output = ""
        while True:
            i = self._session.expect([self._prompt, pexpect.EOF, pexpect.TIMEOUT, "logging out", self.promptmore,expected_param], timeout=timeout)
            #print "Value of i " + str(i)
            if i == 0:
                # Prompt found
                self.last_match = self._session.match
                self.last_output += self._session.before
                break
            if i == 1:
                # EOF
                logger.error("Connection closed %s" % self)
                raise ValueError("Connection Closed")
            elif i == 2:
                # TIMEOUT
                logger.error(str(self._session))
                logger.error("Time Out")
                raise ValueError("Time Out")
            elif i == 3:
                logger.info("Logged out due to inactivity. Reconnecting..")
                self.reconnect()
                self._session.sendline(cmd)
                continue
            elif i == 4:
                # More prompt. Send Space
                self.last_output += self._session.before
                self._session.send(" ")
                continue
            elif i == 5:
                self.last_output = self._session.before
                break

        #logger.debug("Output Before Removing command: %s" % self.last_output)
        #self.last_output = re.sub("(?m)" + re.escape(cmd), "", self.last_output)
        #logger.debug("Output After Removing command: %s" % self.last_output)

        #if not ignoreErrors and re.search("\b:*(error|unable|failed|failure|unrecognized command):*\b", self.last_output, re.I):
        #    logger.error("Error while executing command")

        if cmd.startswith("hadoop"):
            #logger.debug("Before removal: '%s'" % self.last_output)
            self.last_output = re.sub(r"(?m)^\s*WARNING:.*$", "", self.last_output)
            #logger.debug("After removal: '%s'" % self.last_output)

        # Remove some special characters seen in new platforms (gingko onwards)
        #logger.debug("Output before removing special chars: %s" % self.last_output)
        ret_val = remove_special(self.last_output)

        #logger.debug("Output after removing special chars: %s" % ret_val)
        return ret_val.strip()




    def sendMultipleCmd(self, cmds, *args, **kwargs):
        consolidated_output = ""
        for cmd in cmds.split("\n"):
            consolidated_output += self.sendCmd(cmd, *args, **kwargs)
            consolidated_output += "\n"
        return consolidated_output

    def getReturnCode(self):
        """Gets the return code of the last executed command on the node"""
        retcode = self.sendCmd("echo $?")
        try:
            return int(retcode)
        except:
            return retcode

    def getModeForPrompt(self, prompt):
        for k, v in self.prompts.iteritems():
            if v == prompt:
                return k

    def getPromptForMode(self, mode):
        return self.prompts[mode]

    def popMode(self):
        if not self._mode_stack:
            logger.warning("Tried to popMode but Mode Stack is empty. Make sure pushMode was called earlier")
            return None
        prev_mode = self._mode_stack.pop()
        return self.setMode(prev_mode)

    def pushMode(self, targetmode):
        self._mode_stack.append(self.getMode())
        return self.setMode(targetmode)

    def guessMode(self, cmd=False):
        """Guess the mode in which the device is currently in.

        :param cmd: True, if you need to send a newline to get the prompt
        """
        self.resetStream()
        if cmd is True:
            self._session.sendline("")

        i = self._session.expect([pexpect.EOF, pexpect.TIMEOUT] + self.prompts.values())
        if i == 0:
            logger.error("Connection closed")
            raise ValueError("Connection Closed")
        elif i == 1:
            logger.error(str(self._session))
            logger.error("Timeout while waiting for prompt")
            logger.warn(self._session.before)
            raise ValueError("Prompt not found")
        else:
            self._prompt = self._session.match.re
            #logger.debug("Prompt matched: %s" % self._prompt.pattern)
            #logger.debug("Output from device: (%s, %s)" % (self._session.before, self._session.after))
            self._mode = self.getModeForPrompt(self._prompt)
        return self._mode
        
    def getMode(self):
        """Returns the current mode of the device"""
        return self._mode

    def setMode(self, targetmode):
        """Sets a mode on the device.

        The following modes are supported:

        #. enable
        #. config
        #. shell
        #. pmx
        #. mysql
        """
        self.resetStream()

        if targetmode not in self.prompts.keys():
            raise ValueError("Invalid Mode %s" % targetmode)

        initialmode = self.getMode()
        if targetmode == initialmode:
            logger.debug("In %s mode" % targetmode)
            return True

        logger.debug("Changing mode from '%s' to '%s' on %s" % (initialmode, targetmode, self))

        # Provide all permutations of mode switching
        if   targetmode == CLI_MODES.config and initialmode == CLI_MODES.enable:
            self._session.sendline("config terminal")
        elif targetmode == CLI_MODES.config and initialmode == CLI_MODES.shell:
            self._session.sendline("cli -m config")
        elif targetmode == CLI_MODES.config and initialmode == CLI_MODES.pmx:
            self._session.sendline("quit")
        elif targetmode == CLI_MODES.enable and initialmode == CLI_MODES.shell:
            self._session.sendline("cli -m enable")
        elif targetmode == CLI_MODES.enable and initialmode == CLI_MODES.config:
            self._session.sendline("exit")
        elif targetmode == CLI_MODES.shell and initialmode == CLI_MODES.enable:
            self._session.sendline("_shell")
        elif targetmode == CLI_MODES.shell and initialmode == CLI_MODES.config:
            self._session.sendline("_shell")
        elif targetmode == CLI_MODES.shell and initialmode == CLI_MODES.mysql:
            self._session.sendline("quit")
        elif targetmode == CLI_MODES.pmx:
            self.setMode(CLI_MODES.config)
            self._session.sendline("pmx")
        elif targetmode == CLI_MODES.mysql:
            self.setMode(CLI_MODES.shell)
            self._session.sendline("idbmysql")
        elif targetmode != CLI_MODES.config and initialmode == CLI_MODES.pmx:
            # Moving from pmx to other modes. Switch to config and proceed..
            self.setMode(CLI_MODES.config)
            self.setMode(targetmode)
            self._session.sendline("")  # Send empty line for guessMode to work
        elif targetmode != CLI_MODES.shell and initialmode == CLI_MODES.mysql:
            # Moving from mysql to other modes. Switch to shell and proceed..
            self.setMode(CLI_MODES.shell)
            self.setMode(targetmode)
            self._session.sendline("")  # Send empty line for guessMode to work
        else:
            raise ValueError("Invalid Mode combination. Targetmode: %s, Currentmode: %s" % (targetmode, initialmode))

        finalmode = self.guessMode()
        logger.debug("Mode changed to %s mode" % finalmode)
        if targetmode == finalmode:
            if finalmode == CLI_MODES.shell:
                self.initShell()
            return True
        else :
            # A user can be in pmx subshells. So we might need to get back a couple levels
            if finalmode == CLI_MODES.pmx and targetmode == CLI_MODES.config:
                return self.setMode(CLI_MODES.config)
            else:
                logger.warn("Unable to set '%s' mode" % targetmode)
                return False
    


    def isInCluster(self):
        """Check if the node is a part of a TM Cluster"""
        logger.debug("Checking if %s is a part of cluster" % self)
        role = self.getClusterRole()
        return role is not None and role != "DISABLED"

    def isMaster(self):
        """Check if the node is currently the master of Cloudera Cluster"""
        logger.debug("Checking if %s is Cloudera Master" % self)
        is_master = self.getClusterRole()
        logger.debug("Is %s master: %s" % (self, is_master))
        return is_master
   
    def isStandby(self):
        """Check if the node is currently the standby of TM Cluster"""
        logger.debug("Checking if %s is TM Standby" % self)
        is_standby = self.getClusterRole()
        logger.debug("Is %s standby: %s" % (self, is_standby))
        return is_standby







    def command_execution_status(self):
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" not in output2 :
            return "false"
        else:
            return "true"


    def createDirectory(self, summary_handle,directory,mode,role ="",summary_var_dict={}):
        """Creates a directory on the machine

        :param directory: The path of the directory to be created
        """
        if role:
            directory = directory + "/" + role
 
        tmp_var = "mkdir -p %s%s%s" %(directory,self,role)
        if mode == "RECOVERY":
            flag = self.check_var_in_dict(tmp_var,summary_var_dict)
            if flag == "true":
                return

        self.pushMode(CLI_MODES.shell)
        if role:
            self.removePath(directory)

        logger.info ("Directory is %s" %directory)
        output = self.sendCmd("mkdir -p %s" % directory)
        status = self.command_execution_status()
        if status == "true":
            summary_handle.write("mkdir -p %s,%s,%s,pass \n" %(directory,self,role))
        else:
            summary_handle.write("mkdir -p %s,%s,%s,fail \n" %(directory,self,role))        

        self.popMode()
        return output


    def changeDirectory(self, directory):
        """Creates a directory on the machine

        :param directory: The path of the directory to be created
        """
        self.pushMode(CLI_MODES.shell)
        output = self.sendCmd("cd %s" % directory)
        self.popMode()
        if "No such file or directory" in output:
            logger.error ("No such file or directory exist : %s" %directory)
        return output




    def removePath(self, path):
        """Removes a file/directory from the machine

        :param path: The path of the file/directory to be removed

        .. warning::

            This method will forcefully remove (`rm -rf`) the path. Be Careful while calling this method.
        """
        self.pushMode(CLI_MODES.shell)
        output = self.sendCmd("rm -rf %s" % path)
        self.popMode()
        return output

    def put(self, *args, **kwargs):
        """Transfers a file from local machine to the server using :meth:`~.Node.scp`. An alias to :meth:`~.Node.copyFromLocal`"""
        self.copyFromLocal(*args, **kwargs)

    def get(self, *args, **kwargs):
        """Transfers a file from remote server to locaal machine using :meth:`~.Node.scp`. An alias to :meth:`~.Node.copyToLocal`"""
        self.copyToLocal(*args, **kwargs)

    def copyFromLocal(self, local_src, remote_dest):
        """Transfers a file from local machine to the server using :meth:`~.Node.scp`"""
        if not local_src.startswith("/"):
            # If this is not an absolute path, consider it present in potluck's "remote" directory
            for d in (ROOT_DIR, REMOTE_DIR):
                potential_src = os.path.join(d, local_src)
                if os.path.exists(potential_src):
                    local_src = potential_src
                    break
                else:
                    logger.warning("Path '%s' does not exist on local machine" % potential_src)
            else:
                logger.error("Path '%s' does not exist on local machine" % local_src)
                raise ValueError("Path '%s' does not exist on local machine" % local_src)

        # Create parent directory on the remote machine
        remote_parent_dir = os.path.dirname(remote_dest)
        #self.createDirectory(remote_parent_dir)

        logger.info("Copying '%s' from local machine  to %s at '%s'" % (local_src, self.ip, remote_dest))
        return self.scp(local_src, "root@%s:%s" % (self.ip, remote_dest))

    def copyToLocal(self, remote_src, local_dest):
	print "in copytolocal func"
	print "remote_src is:" , remote_src
	print "local_dest is" , local_dest
        """Transfers a file from remote server to local machine using :meth:`~.Node.scp`"""
        if not local_dest.startswith("/"):
            local_dest = os.path.join(REMOTE_DIR, local_dest)
        logger.info("Copying '%s' from '%s' to local machine at '%s'" % (remote_src, self.ip, local_dest))
        parent_dir = os.path.dirname(local_dest)
	print "parent_dir is:",parent_dir
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        return self.scp("root@%s:%s" % (self.ip, remote_src), local_dest)

    def copyRecursiveToLocal(self, rootdir, local_dest):
	cmd =  'find ' + rootdir + ' -type f'
	output = self.sendCmd(cmd)
	newlist = []
	newlist = output.split("\n")
	newlist = newlist[1:-1]
	newlist = [item.replace("\r", "") for item in newlist]
	print "List of files to be copied: ",newlist
	for item in newlist:
		self.copyToLocal(item,local_dest)
    def scp(self, src, dst):
        """Transfers a file to the remote machine using scp

        .. note::

            This method is internally used by copyFromLocal and copyToLocal methods
        """
        scp_cmd = "scp -r %s %s" % (src, dst)
        connect_handle = pexpect.spawn(scp_cmd)
        connect_handle.setwinsize(400,400)
        connect_handle.logfile_read = sys.stdout
        i = 0
        ssh_newkey = r'(?i)Are you sure you want to continue connecting'
        while True:
            i = connect_handle.expect([ssh_newkey, 'assword: ', pexpect.EOF, pexpect.TIMEOUT])
            if i==0:
                connect_handle.sendline('yes')
                continue
            elif i==1:
                 #logger.info("Password supplied")
                 connect_handle.sendline(self.password)
                 continue
            elif i==2:
                logger.info("Scp complete")
                logger.info(connect_handle.before)
		if "No such file or directory" in connect_handle.before:
			report.fail("%s exist on remote server %s" %(src.split(":")[-1],src.split(":")[0].split("@")[1]))
		break
            elif i==3:
                logger.warning("Timeout while waiting for connection")
                logger.info(connect_handle.before) # print out the result
                raise ValueError("Unable to establish connection")
        return True


    def getEpochTime(self, time_str=None):
        """Executes ``date +%s`` command on the node and gets the system time in epoch format

        :param time_str: Get time for this particular datetime string
        :returns: System time in epoch format
        :rtype: float
        """
        self.pushMode(CLI_MODES.shell)
        if time_str is None:
            system_time = self.sendCmd(r"date +%s")
        else:
            system_time = self.sendCmd("date -d '%s' " % time_str + r"+%s")

        try:
            system_time = float(system_time)
            logger.info("Time %f" % system_time)
        except:
            logger.error("Invalid system time '%s' on node '%s'" % (system_time, self))
            raise ValueError("Invalid system time '%s' on node '%s'" % (system_time, self))
        self.popMode()
        return system_time



    def get_master(self,node_alias):
                role = self.getClusterRole()
                if role == 'master':
                        master_namenode = node_alias
                        logger.info("master namenode is %s" %master_namenode)
			return master_namenode

    def getClusterRole(self):
        """Returns this node's role in TM Cluster

        :returns: Node role in upper-case
        """
	list = []
	counter = 0
	f = self.sendCmd("cat /etc/hadoop/conf/hdfs-site.xml")
	list = f.split("\n")
	for line in list:
		counter = counter + 1
		if "dfs.ha.namenodes" in line:
			logger.info("Setup is HA")
			logger.info ("Finding nameservices id")
			a = list[counter]
			nameservice1=a.split("value>")[1].split("<")[0].split(",")[0].strip()
			nameservice2=a.split("value>")[1].split("<")[0].split(",")[1].strip()
	node_ip = self.run_cmd("grep " + nameservice2 + " /etc/hosts | awk '{print $1}'")
        print "==================="
	print "node ip is %s" %node_ip.split("\n")[0]
        print "==================="
        cmd = "ifconfig | grep " + node_ip.split("\n")[0] 
	output = self.run_cmd(cmd)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" not in output2 :
                cmd="/usr/bin/hdfs haadmin -getServiceState " + nameservice2
		role=self.run_cmd(cmd)
		if "active" in role:
			return "master"
		elif "standby" in role:
			return "standby"
		else:
			logger.info("command was not executed successfully.Please check hadoop")
	else:
		print "in else...."
		cmd="/usr/bin/hdfs haadmin -getServiceState " + nameservice1
		role=self.run_cmd(cmd)
		if "active" in role:
			return "master"
		elif "standby" in role:
			return "standby"
		else:
			logger.info("command was not executed successfully.Please check hadoop")
    def checkserviceProcess(self, processname):
        logger.info("Monitoring of process %s" % processname)
        # Connect to the device and get a node object
        logger.info("Checking that %s process is running" % processname)
        self.setMode("shell")
        output = self.sendCmd("service " + processname + " status", ignoreErrors=True)
        if not re.search(r"running|active", output, re.I):
            return (0)
        else:
            return (1)

    def grepProcess(self, ipaddr, processname):
        logger.info("Monitoring of process %s" % processname)
        # Connect to the device and get a node object
        logger.info("Checking that %s process is running" % processname)
        self.setMode("shell")
        #output = self.run_cmd("ps -ef | grep  -i " + '"' + processname + '"')
        output = self.run_cmd("ps -ef | grep  -i " + '"' + processname + '"' + " | grep -v grep ")
        if len(re.findall(r"%s" % processname, output, re.IGNORECASE)) > 0:
            return (1)
        else:
            return (0)

    def connecthbasedb(self, ipaddr, dbdir):
        # Connect to the device and get a node object
        print "connection to device is successful"
        # logger.info("Checking that %s db is connecting" %dbname)
        self.setMode("shell")
        output = self.run_cmd(dbdir + " shell", "0>")
        output = self.run_cmd("list", "0>")
        if re.search(r"hbase\(main\)", output, re.IGNORECASE):
            output = self.run_cmd("exit")
            return (1)
        else:
	    output = self.run_cmd("exit")
            return (0)
    def connecthivedb(self):
        output = self.run_cmd("hive", ">")
        output = self.run_cmd("show databases;", ">")
        if re.search(r"hive", output, re.IGNORECASE):
            output = self.run_cmd("exit;")
            return (1)
        else:
            output = self.run_cmd("exit;")
            return (0)
    def redisProcess(self, ipaddr):
        self.setMode("shell")
        output = self.run_cmd("/opt/redis/src/redis-cli cluster nodes")
        if len(re.findall(r"disconnected", output, re.IGNORECASE)) > 0:
            return (0)
        else:
            return (1)

