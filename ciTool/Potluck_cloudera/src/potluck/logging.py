"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides logging functions.

To use the logging methods, the :obj:`.logger` needs to be imported in the test script

Example Usage::

    from potluck.logging import logger
    logger.info("Hello World!!")

Potluck provides the following debugging levels, which can be used via methods of the logger instance
"""

import sys
from datetime import datetime
import traceback

from potluck.mixins import SingletonMixin

levels = {
    "ERROR" : 1,
    "WARNING" : 2,
    "NOTICE" : 3,
    "INFO" : 4,
    "DEBUG" : 5,
}

class Logger(object):
    """This class embeds the methods used to print log messages
    in a test case.

    Normally, you wouldn't need to create an instance yourself.
    An instance of this class (:obj:`.logger`) is already provided by the framework.
    """
    def __init__(self, stream=None):
        self.stream = stream

    def __call__(self, message):
        return self.info(message)

    def log(self, level, message):
        from potluck.reporting import report
        if self.stream is None:
            stream = sys.stdout
        else:
            stream = self.stream

        message = str(message)
        if level not in levels:
            raise ValueError("Not a valid logging level %s" % level)

        if level == "ERROR":
            report.error(message.split("\n")[0])

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for msg in message.split("\n"):
            stream.write("%s [%s]: %s\n" % (timestamp, level, msg))

    def debug(self, message):
        """Logs a string as a debug message"""
        return self.log("DEBUG", message)

    def info(self, message):
        """Logs a string as an info message"""
        return self.log("INFO", message)

    def warn(self, message):
        """Logs a string as a warning message"""
        return self.log("WARNING", message)

    def warning(self, message):
        """Logs a string as a warning message. Just an alias for .warn
        """
        return self.log("WARNING", message)

    def notice(self, message):
        """Logs a string as a notice message"""
        return self.log("NOTICE", message)

    def error(self, message):
        """Logs a string as an error message.

        Calling this method will mark the testcase as "PASSED WITH ERROR"
        """
        return self.log("ERROR", message)

    def exception(self, message, fatal=True):
        """Prints a traceback of the last encountered exception
        and logs a string as an error message.
        This method should only be called from a try..except block

        Calling this method will mark the testcase as "PASSED WITH ERROR"
        """
        current_exception_type = sys.exc_info()[0]
        if current_exception_type is not None:
            # If called from a `try...except` block, Print the stacktrace
            tb = traceback.format_exc()
            log_msg = "%s\n%s" % (message, tb)
            self.error(log_msg)
            if fatal:
                # If this is a fatal exception, abort the testcase
                from potluck.reporting import report
                report.fail(message)
        else:
            # Simply behave like log error
            self.error(log_msg)

#: An instance of the :obj:`Logger` class, that should be used for logging in the test scripts
#:
#: Example Usage::
#:
#:    from potluck.logging import logger
#:    logger.info("Hello World!!")
logger = Logger()
