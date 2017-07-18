"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Implements Collector node specific APIs
"""

from potluck.nodes.Node import Node
from potluck.logging import logger
from potluck.nodes import CLI_MODES
import re

class CollectorMixin(object):
    def __init__(self, *args, **kwargs):
        super(CollectorMixin, self).__init__(*args, **kwargs)

    def showPmProcessOutput(self, grep=None):
        if grep is None:
            self.pushMode(CLI_MODES.config)
            _show_process_output = self.sendCmd("show pm process collector", ignoreErrors=True)
        else:
            self.pushMode(CLI_MODES.shell)
            _show_process_output = self.sendCmd("cli -m enable -t 'show pm process collector' | grep -i '%s'" % grep, ignoreErrors=True)
        self.popMode()
        return _show_process_output

    def isRunningInReplay(self):
        """
        Returns `True` if the collector's active instance has `-r` param in
        'show pm process collector' command
        """
        logger.info("Checking if collector is running in Relay mode")

        # Extract Collector's instance id
        if re.search(r"Argv\s*:.*\s(-r|--replay)", self.showPmProcessOutput(grep="Argv"), flags=re.I):
            return True
        else:
            return False

    def getActiveInstanceId(self):
        """
        Returns the collector's active instance number using
        'show pm process collector' command
        """
        # Extract Collector's instance id
        m = re.search(r"Argv\s*:.*-i\s*(?P<COL_INSTANCE_ID>\d+)", self.showPmProcessOutput(grep="Argv"), flags=re.I)
        if not m:
            logger.error("Not able to extract instance id commmand's output")
            return None
        collector_instance_id = m.group("COL_INSTANCE_ID")
        logger.debug("Active Instance Id: %s" % collector_instance_id)
        return int(collector_instance_id)

    def getLaunchPath(self):
        """
        Returns the collector's launch path using 'show pm process collector' command
        """
        logger.debug("Getting active collector's launch path")

        # Extract Collector's launch path
        m = re.search(r"Argv\s*:\s*(?P<COL_LAUNCH_PATH>\S+)", self.showPmProcessOutput(grep="Argv"), flags=re.I)
        if not m:
            logger.error("Not able to extract launch path from command's output")
            return None
        launch_path = m.group("COL_LAUNCH_PATH")
        logger.debug("Collector Launch Path: %s" % launch_path)
        return launch_path

    def getConfiguration(self, attribute):
        """
        Returns the collector's configured attribute present in `show run`
        """
        self.pushMode("shell")
        cmd = "cli -m enable -t 'show run' | grep 'collector modify-instance %s' | grep '%s' | head -1 | awk '{print $NF}'" % (self.getActiveInstanceId(), attribute)
        value = self.sendCmd(cmd)
        self.popMode()
        return value

    def getConfiguredBinSize(self):
        """
        Returns the collector's configured attribute present in `show run`
        """
        logger.debug("Getting collector's configured bin size")
        binsize = self.getConfiguration("bin-size")
        try:
            binsize = int(binsize)
            logger.info("Bin size %d" % binsize)
        except:
            logger.error("Invalid Bin Size %s. Taking default as 300" % binsize)
            binsize = 300
        return binsize

    def getConfiguredOutputDirectory(self):
        """
        Returns the collector's configured `output-directory` present in `show run`
        """
        logger.debug("Getting collector's configured output directory")
        return self.getConfiguration("output-directory")

    def getConfiguredOutputDirectoryPrefix(self):
        """
        Returns the collector's configured `output-directory` present in `show run`

        e.g. If output directory is `/data/collector/potluck_regression_netflows/%y/%m/%d/%h/%mi/app.`,
        then this method will return `/data/collector/potluck_regression_netflows/`
        """
        logger.debug("Getting collector's output directory prefix")
        return self.getConfiguredOutputDirectory().split("%y")[0]

    def getConfiguredAdaptors(self):
        self.pushMode(CLI_MODES.shell)
        adaptor_cmd = "cli -m enable -t 'show run' | grep 'collector modify-instance %s add-adaptor' | awk '{print $5}'" % self.getActiveInstanceId()
        adaptors = self.sendCmd(adaptor_cmd)
        self.popMode()
        return adaptors.split()

    def getStats(self, stats_type, adaptor=None):
        """
        Returns the collector stats for the specific `adaptor`. If `adaptor` is not given, 
        then the stats of the first adaptor will be returned

        :param stats_type: Which stats do you want to read
        :param adaptor: The adaptor for which you want to read the stats
        :rtype: int
        """
        if adaptor is None:
            adaptors = self.getConfiguredAdaptors()
            if not adaptors:
                raise ValueError("Cannot get collector stats, because no adaptor is configured")
            # Get stats of first configured adaptor
            adaptor = adaptors[0]

        self.pushMode(CLI_MODES.config)
        logger.info("Getting '%s' stats for '%s' adaptor" % (stats_type, adaptor))
        stats_cmd = "collector stats instance-id %s adaptor-stats %s %s" % (self.getActiveInstanceId(), adaptor, stats_type)
        output = self.sendCmd(stats_cmd)
        self.popMode()
        if output:
            try:
                return float(output)
            except ValueError:
                logger.error("Invalid stats count '%s' on '%s'" % (output, self))
                raise ValueError("Invalid stats count '%s' on '%s'" % (output, self))
        else:
            return 0

class CollectorNode(CollectorMixin, Node):
    pass
