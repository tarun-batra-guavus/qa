"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides the base methods to be used with node handles

Most of the methods are used internally by the framework.
View Source to take a look at all the methods.
"""

import subprocess
import pexpect
import glob
import sys
import re
import time
import commands
import os
import datetime
import subprocess
from optparse import OptionParser
from potluck.logging import logger
from potluck.nodes import CLI_MODES
from potluck.parsing import parser
from potluck.reporting import report
from potluck import utils
from settings import REMOTE_DIR, ROOT_DIR
import threading
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
        self.common = {}
        self.COMMON_CONF = 'COMMON'
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
        self.parser = parser()

    def upgrade(self,summary_handle,role,rpm_keyword,image_url,dir_installer,exit_flag):
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
        cmd1 = "wget -r -np -nH --cut-dirs=%s --reject 'index.html*' %s" %(length,imageurl_final)
        self.sendCmd(cmd1,300) 
        num_files = "ls -lrt *\.rpm  | grep %s-[0-9]  | awk \'{print $NF}\' | xargs ls -t | tail -n1" %rpm_keyword
        output = self.sendCmd(num_files).split("\n")
        for each in output:
           if each.rstrip().endswith("rpm"):
               #logger.info("Starting installation of %s on node %s having role %s" %(each.strip(),self,role))
               #tmpcmd = "yum -y install " + each.rstrip()
               tmpcmd = "yum install tarun"
               output = self.sendCmd(tmpcmd,600)
               time.sleep(30) 
               output1 = self.sendCmd("echo $?").split("\n")
               output2 = [item.replace("\r", "") for item in output1]
               if "0" not in output2 :
                   summary_handle.write("%s,%s,%s,fail \n" %(tmpcmd,self,role))
                   if exit_flag == "yes":
                       report.fail("Installation failed for %s on node %s having role %s with following error message : \n %s" %(each.strip(),self,role,output))
                   else:
                       logger.info("Installation failed for %s on node %s having role %s with following error message : \n %s" %(each.strip(),self,role,output))
               else:
                   summary_handle.write("%s,%s,%s,pass \n" %(tmpcmd,self,role))
                   logger.info("Successful installation of %s on node %s having role %s" %(each.strip(),self,role))


    def stop_process(self,summary_handle,role,process_name,process_command,exit_flag):
        output1 = []
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

    def start_process(self,summary_handle,role,process_name,process_command,exit_flag):
        output1 = []
        self.setMode("shell")
        process_command_new = process_command.replace("stop","start")
        #logger.info ("Starting the process %s on node %s with role %s using command %s"  %(process_name,self,role,process_command_new))
        output = self.sendCmd(process_command_new)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" not in output2  :
            summary_handle.write("%s,%s,%s,%s,fail \n" %(process_name,process_command_new,self,role))
            if exit_flag == "yes":
                report.fail ("Starting the process failed for %s on node %s having role %s with following error message : \n %s" %(process_name,self,role,output))
            else:
                logger.info("Starting the process failed for %s on node %s having role %s with following error message : \n %s" %(process_name,self,role,output))
        else:
            summary_handle.write("%s,%s,%s,%s,pass \n" %(process_name,process_command_new,self,role))
            logger.info ("Successfully Started the process %s on node %s with role %s using command %s"  %(process_name,self,role,process_command_new))




    def stop_job(self,summary_handle,role,listpassed):
        i = 0
        output1 = []
        while i < len(listpassed):
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


    def apply_mop(self,summary_handle,role,mop_command,exit_flag):
        output1 = []
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

    def files_backup(self,summary_handle,role,listpassed,dir_backup):
        i = 0
        output1 = []
        dir_backup_role = dir_backup + "/" + role
        while i < len(listpassed):
            self.setMode("shell")
            #logger.info ("Taking file backup on node %s with role %s for file %s"  %(self,role,listpassed[i+2]))
            cmd3 = "cp %s %s/" %(listpassed[i+2],dir_backup_role)
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





    def copy_backup_files(self,summary_handle,role,listpassed,dir_backup,dir_build_content):
        i = 0
        output1 = []
        dir_role = dir_backup + "/" + role
        dir_build_content_role = dir_build_content + "/" + role
        while i < len(listpassed):
             cmd1 = "cp %s %s/" %(listpassed[i+2],dir_build_content_role)
             output = self.sendCmd(cmd1)
             output1 = self.sendCmd("echo $?").split("\n")
             output2 = [item.replace("\r", "") for item in output1]
             if "0" not in output2 :
                 summary_handle.write("%s,%s,%s,fail \n" %(listpassed[i+2],self,role))
                 if listpassed[i+3] == "yes":
                     report.fail ("Build File backup on node %s having role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output)) 
                 else:
                     logger.info ("Build File backup on node %s having role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
             else:
                 summary_handle.write("%s,%s,%s,pass \n" %(listpassed[i+2],self,role))
                 logger.info ("Successful Build File backup taken on node %s having role %s for file %s "  %(self,role,listpassed[i+2]))
             backup_file_path = dir_role + "/" + listpassed[i+2].split("/")[-1]
             build_file_path = dir_build_content_role + "/" + listpassed[i+2].split("/")[-1]
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



    def checkProcess(self,each,processname):
        logger.info("Monitoring of process %s" % processname)
        self.setMode("shell")
        cmd = "ps -ef | grep -i %s | grep -v grep" %(processname)
        output = self.sendCmd(cmd)
        output1 = self.sendCmd("echo $?").split("\n")
        output2 = [item.replace("\r", "") for item in output1]
        if "0" in output2 :
            report.fail("Following yum process :%s running on node %s with role %s" %(output,self,each))
        else:
            logger.info ("No yum process running on node")

    def merge_files(self,role,listpassed,dir_backup,dir_build_content):
        i = 0
        output1 = []
        dir_role = dir_backup + "/" + role
        dir_build_content_role = dir_build_content + "/" + role
        while i < len(listpassed):
             cmd3 = "cp %s %s/" %(listpassed[i+2],dir_build_content_role)
             output = self.sendCmd(cmd3)
             output1 = self.sendCmd("echo $?").split("\n")
             output2 = [item.replace("\r", "") for item in output1]
             if "0" not in output2 :
                 logger.info ("Build File backup on node %s having role %s for file %s failed with following error %s "  %(self,role,listpassed[i+2],output))
             else:
                 logger.info ("Successful Build File backup taken on node %s having role %s for file %s "  %(self,role,listpassed[i+2]))
             backup_file_path = dir_role + "/" + listpassed[i+2].split("/")[-1]
             build_file_path = listpassed[i+2]
             merged_file_path = "/home/" + listpassed[i+2].split("/")[-1]
             if listpassed[i] == "xml":
                 self.merge_xml_file(backup_file_path,build_file_path,merged_file_path)
             elif listpassed[i] == "text":
                 delimiter =  listpassed[i+1]
                 self.merge_text_file(backup_file_path,build_file_path,merged_file_path,delimiter)
             else:
                 report.fail("Incorrect file format")
             i+=3 
    


    def merge_xml_file(self,backup_file,build_file,merged_file):
        dict_backup = {}
        dict_build = {}
        list_keys_changed_values = {}
        flag = "false"
        logger.info ("Backup File : %s Build file : %s" %(backup_file,build_file))
        self.copyToLocal(backup_file,merged_file)
        #logger.info ("Starting xml parsing for file before upgrade %s" %backup_file)
        dict_backup = self.parser.xmlParsing(merged_file)
        if not dict_backup:
            logger.info( "Xml Parsing failed for file : %s before upgrade" %backup_file)
        else:   
            logger.info( "Xml Parsing succeeded for file : %s before upgrade" %backup_file)
        self.removeLocalPath(merged_file)
        self.copyToLocal(build_file,merged_file)
        #logger.info ("Starting xml parsing for file after upgrade %s" %build_file)
        dict_build = self.parser.xmlParsing(merged_file)
        if not dict_build:
            logger.info( "Xml Parsing failed for file : %s after upgrade" %build_file)
        else:   
            logger.info( "Xml Parsing succeeded for file : %s after upgrade" %build_file)
        list_keys_changed_values = self.dict_compare(dict_build,dict_backup)
        logger.info("Following are the parameters for which value is different before and after upgrade: %s " %list_keys_changed_values)
        if list_keys_changed_values:
            #logger.info("Starting merging for file : %s" %build_file.split("/")[-1])
            flag = self.parser.xmlUpdate(merged_file,list_keys_changed_values,dict_backup,dict_build)
            self.removeLocalPath(merged_file)
            merged_file_updated = merged_file + "_updated"
            if flag == "true":
                self.copyFromLocal(merged_file_updated,build_file)      
                logger.info("Succeeded merging for file : %s" %build_file.split("/")[-1]) 
            else:
                logger.info("Failed merging for file : %s" %build_file.split("/")[-1])
        else:
            logger.info("Merging not required as no value changed before and after upgrade for file: %s" %build_file.split("/")[-1]) 
       



    def merge_text_file(self,backup_file,build_file,merged_file,delimiter):
        dict_backup = {}
        dict_build = {}
        list_keys_changed_values = {}
        flag = "false"
        logger.info ("Backup File : %s Build file : %s" %(backup_file,build_file))
        self.copyToLocal(backup_file,merged_file)
        #logger.info ("Starting text parsing for file %s before upgrade" %backup_file)
        dict_backup = self.parser.textParsing(merged_file,delimiter)
        if not dict_backup:
            logger.info( "Text Parsing failed for file : %s before upgrade" %backup_file)
        else:    
            logger.info( "Text Parsing succeeded for file : %s before upgrade" %backup_file)
        self.removeLocalPath(merged_file)
        self.copyToLocal(build_file,merged_file)
        #logger.info ("Starting text parsing for file after upgrade %s" %build_file)
        dict_build = self.parser.textParsing(merged_file,delimiter)
        if not dict_build:
            logger.info( "Text Parsing failed for file : %s after upgrade" %build_file)
        else:  
            logger.info( "Text Parsing succeeded for file : %s after upgrade" %build_file)
        list_keys_changed_values = self.dict_compare(dict_build,dict_backup)
        logger.info("Following are the parameters for which value is different before and after upgrade: %s " %list_keys_changed_values)
        if list_keys_changed_values:
            #logger.info("Starting merging for file : %s" %build_file.split("/")[-1])
            flag = self.parser.textUpdate(merged_file,list_keys_changed_values,dict_backup,dict_build,delimiter)
            self.removeLocalPath(merged_file)
            merged_file_updated = merged_file + "_updated"
            if flag == "true":
                self.copyFromLocal(merged_file_updated,build_file)     
                logger.info("Succeeded merging for file : %s" %build_file.split("/")[-1])
            else:
                logger.info("Failed merging for file : %s" %build_file.split("/")[-1])
        else: 
            logger.info("Merging not required as no value changed before and after upgrade for file: %s" %build_file.split("/")[-1]) 


    def dict_compare(self,current_dict,past_dict):
        set_current, set_past = set(current_dict.keys()), set(past_dict.keys())
        intersect = set_current.intersection(set_past)
        return list(o for o in intersect if past_dict[o] != current_dict[o])


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
            i = connect_handle.expect([ssh_newkey,'assword:',self.promptshell,
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

    def run_cmd(self,command,timeout=30,ignoreErrors=False):
        custom_expect = '#'
        #print command
        self._session.sendline(command)
        #print output

        #i = self._session.expect([self._prompt, pexpect.EOF, pexpect.TIMEOUT, "logging out", self.promptmore,expected_param], timeout=timeout)
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
                #continue
        elif i == 3:
                # More prompt. Send Space
                self.last_output += self._session.before
                self._session.send(" ")
                #continue
        elif i == 4:
                self.last_output = self._session.before
                logger.info("executed command successfully")

        #logger.debug("Output Before Removing command: %s" % self.last_output)
        self.last_output = re.sub("(?m)" + re.escape(command), "", self.last_output)
        #logger.debug("Output After Removing command: %s" % self.last_output)

        if not ignoreErrors and re.search("\b:*(error|unable|failed|failure|unrecognized command):*\b", self.last_output, re.I):
            logger.error("Error while executing command")

        if command.startswith("hadoop"):
            #logger.debug("Before removal: '%s'" % self.last_output)
            self.last_output = re.sub(r"(?m)^\s*WARNING:.*$", "", self.last_output)
            #logger.debug("After removal: '%s'" % self.last_output)

        # Remove some special characters seen in new platforms (gingko onwards)
        #logger.debug("Output before removing special chars: %s" % self.last_output)
        ret_val = remove_special(self.last_output)
        #logger.debug("Output after removing special chars: %s" % ret_val)
        return ret_val.strip() 



    def sendCmd(self, cmd, timeout=3600, ignoreErrors=False,expected_param = "]#"):
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

        ret_val = self.last_output
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
        is_master = self.getClusterRole() == "MASTER"
        logger.debug("Is %s master: %s" % (self, is_master))
        return is_master
   
    def isStandby(self):
        """Check if the node is currently the standby of TM Cluster"""
        logger.debug("Checking if %s is TM Standby" % self)
        is_standby = self.getClusterRole() == "STANDBY"
        logger.debug("Is %s standby: %s" % (self, is_standby))
        return is_standby


        output = self.sendCmd("image fetch %s" % imageurl, 3600)
        for err in image_fetch_errors:
            if re.search(err, output, re.I):
                logger.error("Image fetch failed")
                return False


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
            filename, filetype = self._extractFileDetails(filename)
            output_list.append({
                "filename" : filename,
                "type" : filetype,
            })
        return output_list

    def createDirectory(self, directory,role =""):
        """Creates a directory on the machine

        :param directory: The path of the directory to be created
        """
        self.pushMode(CLI_MODES.shell)
        if role:
            directory = directory + "/" + role
            self.removePath(directory)
        
        logger.info ("Directory is %s" %directory)
        output = self.sendCmd("mkdir -p %s" % directory)
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



    def removeLocalPath(self,path):
        p1 = subprocess.Popen([path],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = p1.communicate() 


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
        """Transfers a file from remote server to local machine using :meth:`~.Node.scp`"""
        if not local_dest.startswith("/"):
            local_dest = os.path.join(REMOTE_DIR, local_dest)
        logger.info("Copying '%s' from '%s' to local machine at '%s'" % (remote_src, self.ip, local_dest))
        parent_dir = os.path.dirname(local_dest)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        return self.scp("root@%s:%s" % (self.ip, remote_src), local_dest)

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

    def getClusterRole(self):
        """Returns this node's role in TM Cluster

        :returns: Node role in upper-case
        """
	list = []
	counter = 0
	f = self.sendCmd("cat /etc/hadoop/conf/hdfs-site.xml")
	#print f
	list = f.split("\n")
	#print list
	for line in list:
		counter = counter + 1
		if "dfs.ha.namenodes" in line:
			logger.info("Setup is HA")
			logger.info ("Finding nameservices id")
			a = list[counter]
			print line
			print "a: " + a 
			nameservice1=a.split("value>")[1].split("<")[0].split(",")[0].strip()
			nameservice2=a.split("value>")[1].split("<")[0].split(",")[1].strip()
	output = self.sendCmd("hdfs haadmin -getServiceState " + nameservice1)
	#match = re.search(r"active \(running\)", output, re.I):
        match =  re.search(r"active", output, re.I)
        match1 =  re.search(r"standby", output, re.I)
	ROLE = "MASTER"
	if match:
            return ROLE
	elif match1:
	    ROLE = "STANDBY"
            return ROLE
	else:
            logger.error("Unable to get node role from `hdfs haadmin -getServiceState`")
            return None
