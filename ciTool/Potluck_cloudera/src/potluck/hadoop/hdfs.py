"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module implements the hdfs related functionality.

Example::

    from potluck.hadoop import hdfs
    
    # Get the list of files present in a directory
    files = hdfs.list("/tmp")

    # Delete a directory
    hdfs.delete("/tmp")
"""

from potluck.mixins import SingletonMixin
from potluck.nodes import find_master_by_type
from potluck.logging import logger

import re
import os

TEMP_FILENAME = "/tmp/random_file"

class Hdfs(SingletonMixin):
    """This class implements the methods to be used for HDFS related functionalities.

    You wouldn't need to create an object of this class, as the framework already
    exposes all the methods in hdfs module (as seen in the above example)
    """
    @property
    def master_namenode(self):
        if not hasattr(self, "_master_namenode"):
            logger.info("Trying to find master namenode")
            # Find out master namenode
            self._master_namenode = find_master_by_type("namenode")
            if self._master_namenode is None:
                raise ValueError("Unable to find master of the cluster")
        return self._master_namenode

    def run_shell_command(self, cmd, pop=True):
        self.master_namenode.pushMode("shell")
        output = self.master_namenode.sendCmd(cmd)
        if pop is True:
            self.master_namenode.popMode()
        return output

    def run_hdfs_command(self, cmd):
        if not hasattr(self, "hdfs_prefix"):
            self.hdfs_prefix = self.master_namenode.hdfsRoot() + " dfs "
        return self.run_shell_command(self.hdfs_prefix + str(cmd))

    def copy(self, src, dst):
        """Copies a file/directory from one location to another"""
        return self.run_hdfs_command("-cp %s %s" % (src, dst))

    def move(self, src, dst):
        """Moves a file/directory from one location to another"""
        return self.run_hdfs_command("-mv %s %s" % (src, dst))

    def statList(self, directory):
        """Returns a list of files/directories along with their details"""
        output = self.run_hdfs_command("-ls %s | grep -viE 'found .+ items' | awk '{print $5 , $NF}'" % directory)
        if "No such file" in output:
            return []

        # Parse the output
        ret_val = []
        for line in output.split("\n"):
            fields = line.split()
            ret_val.append({
                "name" : fields[1],
                "size" : float(fields[0]),
            })
        return ret_val

    def list(self, directory):
        """Returns a list of files/directories present in a directory"""
        output = self.run_hdfs_command("-ls %s | grep -viE 'found .+ items' | awk '{print $NF}'" % directory)
        if "No such file" in output:
            return []
        return output.split()

    def exists(self, filename):
        """Checks if a file exists on HDFS

        :argument filename: Path to the file/directory
        :returns: True if the file exists, otherwise False
        """
        matching_files = self.list(filename)
        return filename in matching_files

    def cat(self, path):
        """Returns the output of `hadoop fs -cat <path>`

        :argument path: Path to the file
        :returns: Text contents of the file
        """
        return self.run_hdfs_command("-cat '%s'" % path)

    def delete(self, filename, delete_dir=True):
        """Deletes a file/directory from HDFS

        :argument filename: Path to a file or directory
        :argument delete_dir: If delete_dir is False, the command will fail if the target path is a directory
        """
        if delete_dir is True:
            return self.run_hdfs_command("-rmr %s" % filename)
        else:
            return self.run_hdfs_command("-rm %s" % filename)

    def getSize(self, filename):
        """Get the size of a file/directory from HDFS

        :argument filename: Path to a file or directory
        """
        file_size = self.run_hdfs_command("-dus %s | awk '{print $NF}'" % filename)
        try:
            file_size = float(file_size)
            logger.debug("Size of hdfs file '%s': %f" % (filename, file_size))
            return file_size
        except ValueError:
            logger.error("Invalid file size of hdfs file '%s': '%s'" % (filename, file_size))
            return -1

    def getHdfsReport(self):
        """Executes :meth:`getHdfsReport <.NameNodeMixin.getHdfsReport>` on master namenode"""
        return self.master_namenode.getHdfsReport()

    def createDummyFile(self, hdfs_filename, size=1):
        """Creates a random dummy file on the given path on hdfs

        :param hdfs_filename: File path to be created on hdfs. If it already exists, it will be removed first.
        """
        # Create a 1MB dummy file
        logger.info("Creating a %sMB dummy file at '%s'" % (size, TEMP_FILENAME))
        self.run_shell_command("head -c %sM < /dev/urandom > %s" % (size, TEMP_FILENAME))

        # Try to -put the file on HDFS
        logger.info("Copying the file from local to HDFS")
        parent_hdfs_dir = os.path.dirname(hdfs_filename)
        self.run_hdfs_command("-mkdir -p %s" % parent_hdfs_dir)
        output = self.run_hdfs_command("-put %s %s" % (TEMP_FILENAME, hdfs_filename))

        # If the file already exists, remove the existing one
        if "exists" in output:
            logger.info("Target file already exists on HDFS. Removing it..")
            self.delete(hdfs_filename)
            logger.info("Copying the file from local to HDFS")
            output = self.run_hdfs_command("-put %s %s" % (TEMP_FILENAME, hdfs_filename))
        
        if re.search("error|failure|failed|unable", output, re.I):
            logger.error("Error while adding a file to HDFS")
            return False
        else:
            logger.info("Successfully added file to HDFS")
            return True
