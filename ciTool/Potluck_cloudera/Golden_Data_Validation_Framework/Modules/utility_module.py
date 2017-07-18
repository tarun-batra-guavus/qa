import pexpect
import time
import re
import datetime
import sys
import os
import errno
import commands
from datetime import date


class utility():

    def ScpToServer(self,file_path,scp_location,ip_address,username,password):
        expectations = ['[Pp]assword',
           'continue (yes/no)?',
           pexpect.EOF,
           pexpect.TIMEOUT,
           'Name or service not known',
           'Permission denied',
           'No such file or directory',
           'No route to host',
           'Network is unreachable',
           'failure in name resolution',
           'No space left on device'
	   '>'
          ]
        self.child_scp = pexpect.spawn("scp -r %s %s@%s:%s"%(file_path,username,ip_address,scp_location))
        self.child_scp.expect(expectations)
        self.child_scp.sendline(password)
        self.child_scp.expect(expectations)
        print "scp successful"

    def scpSendToSever(self, file_path, scp_location,ip_address,username,password):
        scp_cmd = "scp -r %s %s@%s:%s"%(file_path,username,ip_address,scp_location)
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
                 self.logger.info("Password supplied")
                 connect_handle.sendline(password)
                 continue
            elif i==2:
                self.logger.info("Scp complete")
                self.logger.info(connect_handle.before)
                break
            elif i==3:
                self.logger.warning("Timeout while waiting for connection")
                self.logger.info(connect_handle.before) # print out the result
                raise ValueError("Unable to establish connection")
        return True

    def scpReceiveFromServer(self, file_path, scp_location,ip_address,username,password):
        scp_cmd = "scp -r %s@%s:%s %s"%(username,ip_address,file_path,scp_location)
        print "abhay" + scp_cmd
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
                 self.logger.info("Password supplied")
                 connect_handle.sendline(password)
                 continue
            elif i==2:
                self.logger.info("Scp complete")
                self.logger.info(connect_handle.before)
                break
            elif i==3:
                self.logger.warning("Timeout while waiting for connection")
                self.logger.info(connect_handle.before) # print out the result
                raise ValueError("Unable to establish connection")
        return True

    def UntarFile(self,filename,path,deletionpath):
        child = self.child
        child.sendline("cd " + path)
        child.sendline("#")
        child.sendline("rm -rf " + deletionpath)
        child.sendline("#")
        child.sendline("tar -xf " + filename)
        child.sendline("#")
        self.child = child

    def PutintoHadoop(self,filename,remove_flag,hadooplocationremove,hadooplocationput,path):
        child = self.child
        child.sendline("cd " + path)
        child.sendline("#")
        time.sleep(3)
        if remove_flag == "1":
            child.sendline("hadoop dfs -rmr " + hadooplocationremove)
            child.expect("#")
            time.sleep(5)
        child.sendline("hadoop dfs -put " + filename + " " + hadooplocationput)
        child.expect("#")
        self.logger.info("hadoop dfs -put " + filename + " " + hadooplocationput)
        self.logger.info("Data Put into hdfs successfully")
        time.sleep(5)
        self.child = child


#Unit Test Cases
#test_utility = utility()
#test_utility.scp_send("/Users/abhay.pathak/abcd","/tmp/","192.168.113.188","root","root@123")
