"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides the machinery to use data generators in testcases

To generate data you need to define a data generator profile and create a `DataGenerator` instance.

Example Usage::

    from potluck.data import DataGenerator
    data_generator = DataGenerator(collector_vip, data_profile)
    data_generator.start(60)

"""

import os
import signal
import time

from potluck.logging import logger
from potluck.utils import run_cmd
from potluck.cleanup import cleanup
from settings import MODULES_DIR, SCRIPTS_DIR, SUITES_DIR, ROOT_DIR

class DataGenerator(object):
    """Generates dummy test data using `FakeTS` simulator"""
    def __init__(self, collector_ip, config_file):
        self.fakets_path = os.path.join(MODULES_DIR, "fakets", "fakets.py")
        self.collector_ip = collector_ip
        self._generation_started = False     # To keep track of the generator running in background
        self.popen = None
        if config_file.startswith("/"):
            # If absolute path is specified, take the path as it is
            self.config_file = config_file
            if not os.path.exists(config_file):
                logger.error("FakeTS config file does not exist at '%s'." % self.config_file)
                raise ValueError("FakeTS config file does not exist")
        else:
            # If relative path is mentioned, lookup in following order
            # 1. Relative to the root directory
            # 3. Relative to the testsuite directory
            # 3. Relative to the testcase directory
            # 4. Relative to the fakets/conf directory
            for d in (ROOT_DIR, SUITES_DIR, SCRIPTS_DIR, os.path.join(MODULES_DIR, "fakets", "conf")):
                self.config_file = os.path.join(d, config_file)

                if os.path.isfile(self.config_file):
                    logger.debug("Using FakeTS config file '%s'." % self.config_file)
                    break
                else:
                    logger.warning("FakeTS config file does not exist at '%s'." % self.config_file)
            else:
                raise ValueError("FakeTS config file does not exist")

    def start(self, duration, async=False, terminate_after_script=True):
        """Starts generating the data

        :argument duration: The duration for which the data needs to be generated
        :argument async: If `True`, data generation will start in background and the function returns immedietly
        :argument terminate_after_script: If `True` (the default), data generator will terminate after the script
        """
        self.cmd = "%s -p 1 -r -c %s -d %s -e %s" % (self.fakets_path, self.config_file, duration, self.collector_ip)
        logger.debug(self.cmd)
        if async is True:
            # Run the generator in async mode
            logger.info("Starting FakeTS in async mode")
            self._generation_started = True
            self.popen = run_cmd(self.cmd, async=True)
            if terminate_after_script is True:
                cleanup.scriptAction(self.terminate)
        else:
            # Run the generator
            logger.info("Starting FakeTS in sync mode")
            self._generation_started = True
            output = run_cmd(self.cmd)
            logger.info(output)
            self._generation_started = False
        return True

    @property
    def is_running(self):
        """Returns `True` if the data generator is running in background, else returns `False`"""
        if self._generation_started is True and self.popen is not None:
            retcode = self.popen.poll()
            if retcode is None:
                return True
            else:
                self._generation_started = False
                self.popen = None
                return False
        else:
            return False

    def wait(self):
        """Waits till the data generation is complete"""
        logger.info("Waiting for data generator to finish")
        stdout = ""
        if self.popen is not None:
            stdout, stderr = self.popen.communicate()

        self._generation_started = False
        self.popen = None
        print(stdout)

    def terminate(self):
        """Shuts down the data generation. This method is automatically called as a cleanup action at the end of a script"""
        if self.popen is None:
            logger.info("FakeTS data generator is stopped")
            return
        logger.info("Terminating FakeTS data generator")

        logger.debug("Sending SIGINT")
        self.popen.send_signal(signal.SIGINT)   # Simulate ctrl+c
        time.sleep(10)  # Give the child some breathing time
        
        if self.popen.poll() is None:
            # Send SIGTERM
            logger.debug("Sending SIGTERM")
            self.popen.terminate()
            time.sleep(5)  # Some breathing time
        
        if self.popen.poll() is None:
            logger.debug("Sending SIGKILL")
            self.popen.kill()

        if self.popen.poll() is None:
            logger.error("Unable to terminate data generator")
        else:
            logger.info("Terminated data generator")
            print(self.popen.communicate()[0])
            self.popen = None

        # Last resort. Make sure no orphaned child remains
        kill_cmd = "ps -aef | grep '%s' | awk '{print $2}' | xargs kill -9 " % self.cmd
        logger.info("Running command: %s" % kill_cmd)
        os.system(kill_cmd)
