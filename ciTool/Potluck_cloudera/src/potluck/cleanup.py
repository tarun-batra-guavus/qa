"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides the methods to define cleanup actions

In a test script, you would need to use this module whenever
there is a need to define a cleanup action.
A cleanup action is defined by using any one of :meth:`Cleanup.scriptAction`, :meth:`Cleanup.sectionAction` or :meth:`Cleanup.suiteAction`.

.. note:: All the cleanup actions will be run unconditionally, even if any of the action raises an exception

Example Usage::

    from potluck.cleanup import cleanup

    collector = connect("Collector-1")
    # Terminate the collector
    collector.setMode("config")
    collector.sendCmd("pm process collector terminate")

    # Define a cleanup action to restart collector
    cleanup.suiteAction(collector.setMode, "config")
    cleanup.suiteAction(collector.sendCmd, "pm process collector restart")
"""

from potluck.mixins import SingletonMixin
from potluck.logging import logger

class Cleanup(SingletonMixin):
    """This is a singleton class which provides the methods used
    to define cleanup actions

    Normally, you wouldn't need to create an instance yourself.
    An instance of this class (:obj:`.cleanup`) is already provided by the framework.
    """

    def __init__(self, *args, **kwargs):
        self.script_actions = []
        self.section_actions = []
        self.suite_actions = []

    def action(self, list_, arg):
        logger.info("Adding cleanup action: %s%s" % (arg[0].__name__, arg[1:]))
        list_.append(arg)

    def scriptAction(self, method_or_function, *args, **kwargs):
        """Schedules an action to be executed during cleanup task after each script

        :param method_or_function: Any function or instance method which will be called as a cleanup action
        :param args: Positional arguments to be passed to the action
        :param kwargs: Keyword arguments to be passed to the action
        """
        self.action(self.script_actions, (method_or_function, args, kwargs))

    def sectionAction(self, method_or_function, *args, **kwargs):
        """Schedules an action to be executed during cleanup task after each section

        :param method_or_function: Any function or instance method which will be called as a cleanup action
        :param args: Positional arguments to be passed to the action
        :param kwargs: Keyword arguments to be passed to the action
        """
        self.action(self.section_actions, (method_or_function, args, kwargs))

    def suiteAction(self, method_or_function, *args, **kwargs):
        """Schedules an action to be executed during cleanup task after complete suite

        :param method_or_function: Any function or instance method which will be called as a cleanup action
        :param args: Positional arguments to be passed to the action
        :param kwargs: Keyword arguments to be passed to the action
        """
        self.action(self.suite_actions, (method_or_function, args, kwargs))

    def doCleanup(self, actions):
        for action, args, kwargs in actions:
            try:
                action(*args, **kwargs)
            except Exception as e:
                logger.warning("Exception while running cleanup action: %s(%s, %s)" % (action.__name__, ", ".join(args), kwargs))
                logger.warning(str(e))
        logger.info("Cleanup actions complete")

    def doScriptCleanup(self):
        logger.info("Running script cleanup actions")
        self.doCleanup(self.script_actions)

    def doSectionCleanup(self):
        logger.info("Running section cleanup actions")
        self.doCleanup(self.section_actions)

    def doSuiteCleanup(self):
        logger.info("Running suite cleanup actions")
        self.doCleanup(self.suite_actions)

#: An instance of the :obj:`Cleanup` class, to be used to define cleanup actions
#:
#: Example Usage::
#:
#:    from potluck.cleanup import cleanup
#:
#:    cleanup.scriptAction(node.sendCmd, "pm process collector restart")
cleanup = Cleanup()
