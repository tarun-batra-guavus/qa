"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module defines the UiMixin to be used for Rubix and Rge nodes
"""

from Node import Node
from potluck.logging import logger

import re

class UiMixin(object):
    def __init__(self, *args, **kwargs):
        super(UiMixin, self).__init__(*args, **kwargs)
        self.potluck_dir = "/data/utils/potluck"

    def areProcessesUp(self):
        """Return `True` if both rubixd and tomcat are running on this node, else returns `False`"""
        return self.isRubixdUp() and self.isTomcatUp()

    def isRubixdUp(self):
        """Return `True` if rubixd process is running on this node, else returns `False`"""
        ret_val = True
        logger.info("Checking that rubixd process is running from pm")
        self.pushMode("config")
        output = self.sendCmd("show pm process rubix", ignoreErrors=True)

        if not re.search(r"Current status:\s*running", output, re.I):
            logger.error("Rubixd is not running")
            ret_val = False
        else:
            logger.info("Rubixd is running")

        m = re.search(r"Launch path:\s*(?P<LAUNCH_PATH>\S+)", output, flags=re.I)
        if not m:
            logger.error("Not able to parse launch path from commmand's output")
            ret_val = False
        launch_path = m.group("LAUNCH_PATH")

        logger.info("Checking if rubix process is running on shell")
        self.pushMode("shell")
        output = self.sendCmd("ps -aef | grep -w -i rubixd | grep -v grep")
        if not re.search(launch_path, output, re.I):
            logger.error("Rubixd is not running in shell mode")
            ret_val = False
        else:
            logger.info("Rubixd is running on shell")

        self.popMode()  # Come out of shell mode
        self.popMode()  # Come out of config mode
        return ret_val

    def isTomcatUp(self):
        """Return `True` if tomcat process is running on this node, else returns `False`"""
        ret_val = True
        self.pushMode("shell")
        expected_java_processes_count = 1   # Expected tomcat processes per app
        logger.info("Checking tomcat processes")
        running_java_processes = self.sendCmd("ps -aef | grep java | grep -v grep | grep catalina.startup | grep %s" % self.app)
        running_java_processes_count = len(filter(None, running_java_processes.split("\n")))

        if expected_java_processes_count == running_java_processes_count:
            logger.info("All the expected java processes are running")
        else:
            logger.error("Exepected processes: %s, Running processes: %s" % (expected_java_processes_count, running_java_processes_count))
            logger.error("One or more java processes is not running")
            ret_val = False
        self.popMode()
        return ret_val

    def restartProcess(self):
        """Restarts rubix process and verifies that all the processes came up successfully"""
        self.pushMode("config")
        output = self.sendCmd("pm process rubix restart")

        # Give the system some time to converge
        time.sleep(60)

        if self.areProcessesUp():
            logger.info("All processes came up")
            ret_val = True
        else:
            logger.warn("Rubix processes did not come up after restart")
            ret_val = False

        self.popMode()
        return ret_val

    def terminateProcess(self):
        """Terminates rubix process and verifies that all the processes really got killed"""
        self.pushMode("config")
        output = self.sendCmd("pm process rubix terminate")

        # Give the system some time to converge
        time.sleep(60)

        if self.isRubixdUp() or self.isTomcatUp():
            logger.warn("Rubix processes did not die after terminate")
            ret_val = False
        else:
            logger.info("All processes died")
            ret_val = True

        self.popMode()
        return ret_val

class RgeMixin(UiMixin):
    pass

class RubixMixin(UiMixin):
    pass
