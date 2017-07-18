"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module implements the oozie related functionality.

Example::

    from potluck.hadoop import oozie
    
    # Get the list of all running jobs
    files = oozie.getRunningJobs()
"""

from potluck.mixins import SingletonMixin
from potluck.nodes import connect_multiple, get_nodes_by_type, find_master
from potluck.logging import logger

import re
import os

class Oozie(SingletonMixin):
    """This class implements the methods to be used for Oozie related functionalities.

    You wouldn't need to create an object of this class, as the framework already
    exposes all the methods in oozie module (as seen in the above example)
    """

    @property
    def master_namenode(self):
        if not hasattr(self, "_master_namenode"):
            logger.info("Trying to find master namenode")
            namenode_alias_list = get_nodes_by_type("namenode")
            namenodes = connect_multiple(namenode_alias_list)

            # Find out master namenode
            self._master_namenode = find_master(namenodes)
        return self._master_namenode

    def run_shell_command(self, cmd, pop=True):
        self.master_namenode.pushMode("shell")
        output = self.master_namenode.sendCmd(cmd)
        if pop is True:
            self.master_namenode.popMode()
        return output

    def run_pmx_command(self, cmd, pop=True, timeout=300):
        self.master_namenode.pushMode("pmx")
        self.master_namenode.sendCmd("subshell oozie")
        output = self.master_namenode.sendCmd(cmd, timeout)
        if pop is True:
            self.master_namenode.popMode()
        return output

    def parseJobs(self, output):
        jobs = []
        if re.search("No Jobs", output, flags=re.I):
            logger.notice("There are no jobs matching the criteria")
            return jobs

        for line in output.split("\n"):
            if "-----------------------" in line:
                continue
            elif re.search("Next Materialized|Job ID.*App Name", line, flags=re.I):
                continue
            else:
                #0001043-140808091909104-oozie-admi-C     BaseJob_spark  RUNNING   60   MINUTE       2014-08-12 09:00 GMT    2014-08-12 11:00 GMT
                fields = line.strip().split()
                jobs.append({
                    "id" : fields[0],
                    "name" : fields[1],
                    "status" : fields[12].upper(),
                })
        return jobs

    def parseJobInfo(self, output):
        # Job ID : 0001053-140808091909104-oozie-admi-C
        # ------------------------------------------------------------------------------------------------------------------------------------
        # Job Name    : BaseJob_spark
        # App Path    : hdfs://yarnNameService/oozie/BaseJob_spark/
        # Status      : SUCCEEDED
        # Start Time  : 2014-08-12 09:00 GMT
        # End Time    : 2014-08-12 11:30 GMT
        # Pause Time  : -
        # Concurrency : 1
        # ------------------------------------------------------------------------------------------------------------------------------------
        # ID                                         Status    Ext ID                               Err Code  Created              Nominal Time         
        # 0001053-140808091909104-oozie-admi-C@1     SUCCEEDED 0001054-140808091909104-oozie-admi-W -         2014-08-12 11:25 GMT 2014-08-12 09:00 GMT 
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 0001053-140808091909104-oozie-admi-C@2     SUCCEEDED 0001055-140808091909104-oozie-admi-W -         2014-08-12 11:30 GMT 2014-08-12 10:00 GMT 
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 0001053-140808091909104-oozie-admi-C@3     SUCCEEDED 0001059-140808091909104-oozie-admi-W -         2014-08-12 11:35 GMT 2014-08-12 11:00 GMT 
        # ------------------------------------------------------------------------------------------------------------------------------------
        ret_val = {
            "iterations" : []
        }
        ret_val["id"]     = re.search("Job ID\s*:\s*(?P<VALUE>\S+)", output, flags=re.I).group("VALUE")
        ret_val["name"]   = re.search("Job Name\s*:\s*(?P<VALUE>\S+)", output, flags=re.I).group("VALUE")
        ret_val["status"] = re.search("Status\s*:\s*(?P<VALUE>\S+)", output, flags=re.I).group("VALUE").upper()
        ret_val["path"]   = re.search("App Path\s*:\s*(?P<VALUE>\S+)", output, flags=re.I).group("VALUE")

        start_reading_iterations = False
        for line in output.split("\n"):
            if "ID" in line and "Status" in line and "Created" in line:
                start_reading_iterations = True
                continue
            elif start_reading_iterations is False:
                continue

            # Start reading the job iterations
            if "------------------" in line:
                continue
            else:
                #0001053-140808091909104-oozie-admi-C@1     SUCCEEDED 0001054-140808091909104-oozie-admi-W -         2014-08-12 11:25 GMT 2014-08-12 09:00 GMT
                fields = line.strip().split()
                ret_val["iterations"].append({
                    "status" : fields[1].upper(),
                    "id" : fields[2],
                })
        return ret_val

    def getCoordinatorJobs(self, status=None):
        """Get the list and information of all the coordinator jobs

        :param status: Filter jobs with this status
        """
        #cmd = "/opt/oozie/bin/oozie jobs -oozie http://localhost:8080/oozie -jobtype coordinator"
        #if status is not None:
            #cmd += " -filter 'status=" + status.upper() + "'"
        logger.info("Getting information of coordinator jobs")
        if status is None:
            status = "all"
        else:
            status = status.upper()

        cmd = "show coordinator " + status + " jobs"

        output = self.run_pmx_command(cmd)
        return self.parseJobs(output)

    def getJobInfo(self, job_name):
        """Get information about the latest execution of a job

        :param job_name: Name of the job whose information you want to read
        """
        # Extract the ID of the coordinator job of corresponding name
        co_jobs = self.getCoordinatorJobs()
        job_id = None
        for job in co_jobs:
            if job["name"].lower() == job_name.lower():
                job_id = job["id"]
                break
        else:
            logger.error("Job '%s' has never been run" % job_name)
            return None

        cmd = "/opt/oozie/bin/oozie job -oozie http://localhost:8080/oozie -info %s" % job_id
        output = self.run_shell_command(cmd)
        return self.parseJobInfo(output)

    def runJob(self, job_name):
        """Runs a job
        
        :param job_name: Name of the job to run
        """
        return self.run_pmx_command("run job %s" % job_name)

    def stopJob(self, job_name):
        """Stops a job
        
        :param job_name: Name of the job to stop
        """
        return self.run_pmx_command("stop jobname %s" % job_name)

    def rollbackJob(self, job_name):
        """Rollbacks a job
        
        :param job_name: Name of the job to rollback
        """
        return self.run_pmx_command("rollback job %s" % job_name, timeout=600)  # Sometimes it takes longer to rollback a job

    def printLogs(self, job_id, tail=100):
        """Prints the `tail` of a job's logs
        
        :param job_id: ID of the job
        :param tail: Number of lines to be tailed (Default: 100)
        """
        logger.info("Tailing Job stdout logs")
        self.run_shell_command("tail -n %s /data/oozie-admi/%s/*/*out" % (tail, job_id))
        logger.info("Tailing Job stderr logs")
        self.run_shell_command("tail -n %s /data/oozie-admi/%s/*/*err" % (tail, job_id))
