"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides functions related to testcase execution. Some of these can be used in the scripts, other are supposed to be used by the framework.

Example Usage::

    from potluck.testing import call_testcase
    call_testcase("ui/appreflex/login.sikuli")
"""

import potluck
from keyword import KeywordBasedTest
from ui import SikuliTest
from cli import CliTest
from remoting import RemoteTest

import os
import sys
from settings import SCRIPTS_DIR
from potluck.logging import logger
#from potluck.ui import UiTestcase

def run_script(script, *args, **kwargs):
    # Call in a function to limit the scope of any vars defined
    tc_extension = os.path.splitext(script)[-1].lower()
    if tc_extension == ".csv":
        # Keyword based testing
        test = KeywordBasedTest(script)
    elif tc_extension == ".sikuli":
        # Sikuli based Frontend testcases
        test = SikuliTest(script, *args, **kwargs)
    elif tc_extension == ".py":
        # CLI based test testcases
        test = CliTest(script)
    else:
        # Testcase with any other extension is assumed to be remothing testcase
        test = RemoteTest(script)
    test.run()

def call_testcase(testcase_path, suppress_cleanup=True, suppress_pass=True):
    """Calls a test script from within another test script
    
    Supports only sikuli testcases for now.
    
    :argument testcase_path: Path of the testcase
    :argument suppress_cleanup: Whether cleanup of the child-testcase should be suppressed or not
    """
    logger.info("Calling another testcase '%s'" % testcase_path)
    absolute_testcase_path = os.path.abspath(os.path.join(SCRIPTS_DIR, testcase_path))
    tc_name = os.path.split(testcase_path)[-1]

    if potluck.IS_SIKULI is True:
        from potluck.ui import ui
        from potluck import sikuli
        if not testcase_path.endswith(".sikuli"):
            ui.failed("Only sikuli testcases can be called from sikuli environment")

        module_name = os.path.splitext(tc_name)[0]
        module_path = os.path.dirname(absolute_testcase_path)

        #1. Import approach. The problem is that we cannot set sikuli environment before importing the testcase
        """
        # Keep track if we are modifying sys.path
        path_added = False
        if module_path not in sys.path:
            sys.path.append(module_path)
            path_added = True

        print dir(sikuli)
        print sikuli.__dict__
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                reload(module)
            else:
                __import__(module_name)
        finally:
            # If we explicitly added the path, remove it
            if path_added is True:
                sys.path.remove(module_path)
        """

        #2. Execfile approach. Good-to-go
        python_file_path = os.path.join(absolute_testcase_path, module_name + ".py")
        try:
            # Add custom images path for the included testcase
            image_path_added = False
            if absolute_testcase_path not in list(sikuli.getImagePath()):
                sikuli.addImagePath(absolute_testcase_path)
                image_path_added = True

            # Mark the ui testcase to *not* call the cleanup function
            pass_suppressed = False
            if suppress_pass is True and potluck.ui.ui.suppress_pass is False:
                potluck.ui.ui.suppress_pass = True
                pass_suppressed = True

            # Mark the ui testcase to *not* call the cleanup function
            cleanup_suppressed = False
            if suppress_cleanup is True and potluck.ui.ui.suppress_cleanup is False:
                potluck.ui.ui.suppress_cleanup = True
                cleanup_suppressed = True

            # Include sikuli names in the testcase's environment
            # This is equivalent to `from sikuli import *` in the called script
            tc_locals = sikuli.__dict__.copy()
            execfile(python_file_path, tc_locals, tc_locals)
        finally:
            # Revert the changes done earlier
            if image_path_added is True:
                sikuli.removeImagePath(absolute_testcase_path)

            if cleanup_suppressed is True:
                potluck.ui.ui.suppress_cleanup = False

            if pass_suppressed is True:
                potluck.ui.ui.suppress_pass = False
    else:
        # IS_SIKULI is False
        logger.error("Non-Sikuli testcases not yet supported")
