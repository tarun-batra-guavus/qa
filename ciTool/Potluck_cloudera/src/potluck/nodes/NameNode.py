"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Implements Namenode specific APIs
"""

from potluck.nodes.Node import Node
from potluck.logging import logger
import re

hadoop_root = "/opt/hadoop/bin/hadoop"
yarn_root = "/opt/hadoop/bin/hdfs"

class NameNodeMixin(object):
    def __init__(self, *args, **kwargs):
        super(NameNodeMixin, self).__init__(*args, **kwargs)
        self.isYarn = self._isYarn()

    def _isYarn(self):
        self.pushMode("shell")
        #output = self.sendCmd("cli -m config -t 'show run full' | grep '/tps/process/hadoop_yarn value string hadoop_yarn'")
        self.popMode()
        #result = '/tps/process/hadoop_yarn' in output
        #logger.info("Platform is Yarn? %s" % "Yes" if result else "No")
        #return result

    def hdfsRoot(self):
        return (yarn_root if self.isYarn else hadoop_root)

#       for match in re.finditer(r"Insta instance (\d+) service status\s*:\s*([\w ]+)", output, re.I):
#            instance_id = match.group(1)
#            ret_dict["ServiceStatus"][instance_id] = match.group(2).strip().upper()


    def getYarnReport(self):
        """Executes ``yarn node -list `` command, and returns the parsed output
        """
        self.pushMode("shell")
        unhealthyNodes =[]
        ret_dict = {
            "TotalNodes" : 0,
            "UnHealthyNodes" :  [],
            "UnderReplicatedBlocks" : 0,
            "MissingBlocks" : 0
        }
        unhealthyNodes =[]
        hdfs_report_output = self.sendCmd("yarn node -list")
        match = re.search(r"Total Nodes:(\d+)", hdfs_report_output, re.I)
        if match:
            ret_dict["TotalNodes"] = int(match.group(1)) 
 
        for match1 in re.finditer(r"\s+([\S]+):(\d+)\s*([\w]+)\s*(\1):", hdfs_report_output, re.I):
            if match1:
                if match1.group(3) != "RUNNING" :
                    if unhealthyNodes:
                        unhealthyNodes.append(match1.group(1))
                    else:
                        unhealthyNodes = [match1.group(1)]
                    print unhealthyNodes
            else:
                logger.info("Unable to find Data node counts for hdfs")
        ret_dict["UnHealthyNodes"] = unhealthyNodes

        #logger.debug("HDFS Report: %r" % ret_dict)
        self.popMode()
        return ret_dict





    def getHdfsReport(self):
        """Executes ``hadoop dfsadmin -report`` command, and returns the parsed output

        **Returns**: A dict in the following format::

            {
                "AvailableNodes" : 0,
                "TotalNodes" : 0,
                "DeadNodes" : 0,
                "UnderReplicatedBlocks" : 0,
                "MissingBlocks" : 0
            }
        """
        self.pushMode("shell")
        ret_dict = {
            "AvailableNodes" : 0,
            "TotalNodes" : 0,
            "DeadNodes" : 0,
            "UnderReplicatedBlocks" : 0,
            "MissingBlocks" : 0
        }
        hdfs_report_output = self.sendCmd(self.hdfsRoot() + " dfsadmin -report")
        match = re.search(r"Datanodes available:\s*(\d+)\s*\((\d+)\s*total,\s*(\d+)\s*dead\)", hdfs_report_output, re.I)
        if match:
            ret_dict["AvailableNodes"] = int(match.group(1))
            ret_dict["TotalNodes"] = int(match.group(2))
            ret_dict["DeadNodes"] = int(match.group(3))
        else:
            logger.error("Unable to find Data node counts for hdfs")

        # Get other parameters
        match = re.search(r"Under replicated blocks\s*:\s*(\d+)", hdfs_report_output, re.I)
        if match:
            ret_dict["UnderReplicatedBlocks"] = int(match.group(1))
        else:
            logger.error("Unable to find under-replicated blocks for hdfs")

        match = re.search(r"Missing blocks\s*:\s*(\d+)", hdfs_report_output, re.I)
        if match:
            ret_dict["MissingBlocks"] = int(match.group(1))
        else:
            logger.error("Unable to find missing blocks for hdfs")

        #logger.debug(for e in ret_dict])
        logger.debug("HDFS Report: %r" % ret_dict)
        self.popMode()
        return ret_dict

class NameNode(NameNodeMixin, Node):
    pass
