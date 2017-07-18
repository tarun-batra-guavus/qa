"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module contains the helper functions to be used by Sikuli Test cases

To use this in a sikuli testcase, include the following line at the top of
sikuli script::

    from potluck.ui import ui

    try:
        ui.launchBrowser()
        # Do something in the browser

        ui.passed()     # Required if you need to mark the test case as passed
    except:
        ui.failed()
    finally:
        ui.cleanup()

Once the :obj:`ui` object is imported in the testcase, you are free to use the
APIs provided by this module
"""

import os
import shutil
import sys
import traceback
from settings import TMP_DIR
from os.path import dirname
import pickle

import potluck
from potluck import sikuli  # Sikuli module
from potluck import utils
from potluck.logging import logger
from potluck.exceptions import TcFailedException

UI_DIR = os.path.abspath(dirname(__file__))
CUSTOM_IMAGES_PATH = os.path.join(UI_DIR, "images")

if not potluck.IS_SIKULI:
    print("Module imported from Non-Sikuli environment. Methods may fail..")

# Note down the platform for later use
platform = utils.platform()

class UiTestcase(object):
    """This is a singleton class which provides the methods to be used
    in sikuli test scripts

    Normally, you wouldn't need to create an instance yourself.
    An instance of this class (:obj:`potluck.ui.ui`) is already provided by the framework.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super(UiTestcase, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, **kwargs):
        self.browser = None
        self.browser_title = "Firefox"
        self.url = ""
        self.suppress_cleanup = False
        self.suppress_pass = False
        self.config = {}

        # Set the attributes from kwargs
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        # If a url is specified on CLI, take it
        if len(sys.argv) >= 2:
            self.url = sys.argv[1]

        if len(sys.argv) >= 3:
            config_fd = None
            try:
                # Load the config from the file dumped by UI server
                config_fd = open(sys.argv[2])
                self.config = pickle.load(config_fd)
            except:
                logger.error("Unable to load config from config file")
            finally:
                if config_fd is not None:
                    config_fd.close()

    def setup(self):
        # Setup custom images path for common images
        if CUSTOM_IMAGES_PATH not in list(sikuli.getImagePath()):
            sikuli.addImagePath(CUSTOM_IMAGES_PATH)

        sikuli.setAutoWaitTimeout(10)   # Wait for 10 seconds for any pattern to exist

    def launchBrowser(self, url=None):
        """Launches the firefox browser, and opens the `url` in it

        if `url` is none, the url passed on the command line (most probably from
        the Potluck harness) will be used
        """
        self.setup()
        if not url:
            url = self.url

        logger.info("Closing any existing browser window with title '%s'" % self.browser_title)
        self.closeBrowser()
        sikuli.wait(2)

        # Platform specific path
        if platform == "WIN":
            browser_path = r"""cmd.exe /C "start firefox -height 1024 -width 1280" """
        elif platform == "OSX":
            browser_path = "open /Applications/Firefox.app --args -height 1024 -width 1280"
        else:
            browser_path = "firefox -height 1024 -width 1280 &"

        logger.info("Launching browser")
        browser = sikuli.run(browser_path)
        sikuli.wait(5)

        if sikuli.exists("firefox_safe_mode.png", 2):
            logger.info("Closing safe mode prompt")
            sikuli.type(sikuli.Key.ENTER)
            sikuli.wait(5)

        # Bring the browser in focus
        sikuli.App.focus(self.browser_title)

        if platform == "OSX":
            sikuli.type("l", sikuli.KeyModifier.CMD)
        else:
            sikuli.type("l", sikuli.KeyModifier.CTRL)

        # Entering the URL
        logger.info("Opening URL: %s" % url)
        sikuli.type(url + sikuli.Key.ENTER)
        sikuli.wait(5)

        self.browser = browser
        return browser

    def closeBrowser(self):
        """Closes the firefox windows.

        This method is automatically called from the :meth:`cleanup` method.
        So, you wouldn't need to call it explicitly
        """
        logger.info("Closing window with title: %s" % self.browser_title)
        browser = sikuli.App(self.browser_title)
        browser_window = browser.window()
        if browser_window != None:
            browser.focus()
            sikuli.wait(1)
            if platform == "OSX":
                sikuli.type("q", sikuli.KeyModifier.CMD)
            elif platform == "WIN":
                sikuli.type(sikuli.Key.F4, sikuli.KeyModifier.ALT)
            else:
                sikuli.type("q", sikuli.KeyModifier.CTRL)
            sikuli.wait(2)

    def cleanup(self):
        """Performs the required cleanup functions after a Sikuli testcase has completed"""
        # Check if we need to suppress the cleanup
        if self.suppress_cleanup is True:
            logger.info("Suppressing Cleanup. Not closing browser window.")
            return True

        # Do the cleanup
        self.closeBrowser()

    def takeScreenshot(self):
        file_path = sikuli.capture(sikuli.getBounds())
        filename = os.path.basename(file_path)
        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR)
        tmp_path = os.path.join(TMP_DIR, filename)
        shutil.copy(file_path, tmp_path)
        logger.info("Screenshot placed at: %s" % tmp_path)

    def passed(self):
        """Marks the testcase as PASSED"""
        if self.suppress_pass is False:
            print("TESTCASE PASSED")
    
    def failed(self, message=""):
        """Marks the testcase as FAILED, and aborts the script execution

        Whenever this method is called, it takes a screenshot of the desktop
        so the tester can figure out the failure point of the test case
        """
        logger.error(message)
        logger.error("TESTCASE FAILED")
        self.takeScreenshot()
        exception = sys.exc_info()
        if exception[0] != None:
            traceback.print_exception(*exception)
        raise TcFailedException
    
#: An instance of the :obj:`UiTestcase` class, to be used in Sikuli testcases
#:
#: Example::
#:
#:     from potluck.ui import ui
#:     
#:     ui.launchBrowser()
#:     # Do some UI Tasks
#:     ui.cleanup()
ui = UiTestcase()
