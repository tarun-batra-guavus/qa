'''
This module consist all the functions bodies used in the Mapreduce test cases
To apply these need to be import in test script using import from potluck.MR
'''
from potluck.logging import logger
from potluck.reporting import report
from potluck import env
from potluck.nodes import connect, get_nodes_by_type, find_master
import re


namenodes = get_nodes_by_type("NameNode")
master_namenode=find_master(namenodes)



############this function will check for _DONE and _SUCCESS at joboutput path
def getjobresult(outputpath):
    if "_DONE" and "_SUCCESS" in outputpath:
        return 1
    else:
        return 0

########### this will return job id in below format
####        0000007-150511081712574-oozie-admi- , please put W in path where ever using this code
###########

#jobname=env.config.jobname

def getjobid(jobname):

    workflow_out = master_namenode.sendCmd("show workflow RUNNING jobs" , ignoreErrors=True)
    if jobname in workflow_out:
        jobid= re.search(r'(.*)\w\s+'+jobname,workflow_out, flags=re.I).group(1)
        logger.info("job id is "+jobid)
        return jobid
    else:
        return 0
##########################################################################

"""
Provided oozie-id below will return the yarn application ID correspoding to a runnig oozie job
Also return if job is launched on yarn cluster

NOTE:- make sure yarn logs level is INFO in /opt/sample/yarn_conf/log4j.properties
"""
#jobname=env.config.job_name

def appid(joboozieid):          ## provide job's oozie id as input to def
    stdoutfile= master_namenode.sendCmd("cat /data/oozie-admi/"+joboozieid+"W/*/*out")
    if "No such file or directory" in stdoutfile:
        report.fail("please check if job still running in workflow")
    else:
        if "Spark job failed" in stdoutfile:
            report.fail("spark job launched but failed")
        elif "sleeping" in stdoutfile:
            report.fail("falied to submit spark job, please check configuration")
        elif "spark-submit" in stdoutfile:
            logger.info("job successfully submitted on spark")

    stderrfile=master_namenode.sendCmd("grep -i 'Application report for' /data/oozie-admi/"+joboozieid+"W/masterJob--ssh/*err | head -1")
    applicationId= re.search(r'\sfor\s(.*)\s\(state',stderrfile).group(1)
    return (applicationId)    




##########################################################################
####Below class is for the snmp traps (raised, repeat, clear)

class snmp():
    def trap_raised(self, type_of_trap):
        type_of_trap=self.type_of_trap
        if type_of_trap in master.sendcmd("hdfs dfs -ls /data/traps/"+type_of_trap):
            logger.info("traps raised successfully")
        else:
            report.fail("traps did not rasied")
    def trap_clear(self,type_of_trap):
        if type_of_trap in master.sendcmd("hdfs dfs -ls /data/traps/"+type_of_trap):
            logger.info("traps successfully cleared")
        else:
            report.fail("trap did not cleared")
    def trap_repeat(self,type_of_trap):
        if type_of_trap in master.sendcmd("hdfs dfs -ls /data/traps/"+type_of_trap):
            logger.info("traps successfully cleared")
        else:
            report.fail("trap did not cleared")

snmp_check=snmp()
