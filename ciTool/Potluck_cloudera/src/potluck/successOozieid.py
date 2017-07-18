"""
This function will reaturn the oozie id for the running job mentioned in the jobname variable.

"""

from potluck.nodes import connect, get_nodes_by_type, find_master
from potluck.logging import logger
from potluck.reporting import report
from potluck import env
import re
import time
import sys
import subprocess

namenodes = get_nodes_by_type("NameNode")
master_namenode=find_master(namenodes)
master_namenode.setMode("pmx")
master_namenode.sendCmd("subshell oozie")

jobName=env.config.jobname
logger.info("jobname is: "+jobName)
#workflow = master_namenode.sendCmd("show workflow SUCCEEDED jobs" , ignoreErrors=True)
def getsuccessjobid(workflow,jobName):
    logger.info("Success jobname is: "+jobName)
    if jobName in workflow:
        logger.info("Jobname is there in workflow")
        jobid= re.search(r'(.*)\w\s+'+jobName,workflow, flags=re.I).group(1)
        logger.info("Success job id is "+jobid)
        return jobid
    else:
        report.fail("No job running with name:"+jobName)


#jobid=getjobid(workflow,jobName)

