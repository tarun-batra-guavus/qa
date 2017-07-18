#!/usr/bin/env python
##########
# FILE: harness.py
#
# PURPOSE
# -------
# This harness is the main entry point for execution.
# 
# AUTHOR
# ------
# Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>
#
# MODIFICATION HISTORY
# --------------------
# 01-Feb-2013 - sandep.nanda - Initial Creation
#
##########


###################################
# No User-defined variables are present here
# Change `settings.py` if required
###################################
from settings import *

import sys
import subprocess
import os
import re
import traceback
from datetime import datetime
import optparse


from potluck.logging import Logger, logger
from potluck.reporting import report
from potluck import utils
from potluck import env
from potluck import nodes
from potluck.nodes import connect, get_nodes_by_type
from potluck import env

# Parse command line options
parser = optparse.OptionParser()
parser.add_option("-t", "--testbed", dest="testbed",
                  help="Testbed to use for testing [MANDATORY]")
parser.add_option("-m", "--mode", dest="mode",
                  help="Please enter the mode in which you want to run Potluck.Enter H for healthcheck,R for regression rool,U for auto upgrade,HR for healthcheck and regression tool in integrated mode,UH for auto upgrade and healthcheck in integrated mode and ALL for running auto upgrade,healthcheck and regresson tool in integrated mode. [MANDATORY]")
parser.add_option("-e", "--mail_to", dest="mail_to",
                  help="Comma Separated email ids of people whom to send the report")
parser.add_option("-f", "--failure_mode", dest="failure_mode",
                  help="User has to provide this option only when he/she is using the tool in integrated mode like 'HR','UH' or 'ALL'.Enter y for the tool to continue even if healthcheck/upgrade/regression fails.Enter n for tool to exit if healthcheck/upgrade/regression.For eg in 'HR' mode if u give -f with y then even if healthcheck fails,tool will not exit and start the regression tool.And if -f with n is given, the tool will exit and regression will not run.")
parser.add_option("--shell", action="store_true", dest="shell",
                  help=optparse.SUPPRESS_HELP)

(options, args) = parser.parse_args()

harness_logger = Logger(sys.stderr)
if not options.mode:
	harness_logger.error("Mode is a mandatory argument. Use 'run_potluck.py --help'")
        parser.print_help()
        exit(1)
if options.mode == "HR" or options.mode == "UH" or options.mode == "ALL":
	if not options.failure_mode:
		harness_logger.error("Failure mode is a mandatory argument. Use 'run_potluck.py --help'")
        	parser.print_help()
        	exit(1)
if not options.mode == "R":
	if not options.testbed:
        	harness_logger.error("Testbed is a mandatory argument. Use 'harness.py --help'")
        	parser.print_help()
        	exit(1)
if not options.mode == "R":
	if not options.mail_to:
        	harness_logger.error("Mail is a mandatory argument. Use 'harness.py --help'")
        	parser.print_help()
        	exit(1)

# Parse mode
mode = options.mode
testbed = options.testbed
if options.failure_mode:
	flag = options.failure_mode
mail_recp = options.mail_to
print "mode is :",mode

if mode == "H":
	print ("Starting Healthcheck test on Testbed provided") 
	os.system("./harness -e " + mail_recp + " -s Testsuites/CARE/healthcheck.xml -t" + testbed )
if mode == "U":
	print ("Starting Auto Upgrade on Testbed provided") 
	os.system("./harness -e " + mail_recp + " -s Testsuites/DCT_Upgrade/upgrade.xml -t" + testbed)
if mode == "R":
	print ("Starting Regression tool") 
	os.chdir("Golden_Data_Validation_Framework/Test_Driver")
        os.system("python driver.py")
if mode == "HR":
	print ("Starting tool in Integrated mode of Healthcheck and Regression") 
	print ("Starting Healthcheck on Testbed provided....") 
	os.system("./harness -e " + mail_recp + " -s Testsuites/CARE/healthcheck.xml -t" + testbed + " -a" +  mode  + " -f" + flag)
if mode == "UH":
	print ("Starting tool in Integrated mode of Upgrade and Healthcheck")
	os.system("./harness -e " + mail_recp + " -s Testsuites/DCT_Upgrade/upgrade.xml -t" + testbed + " -a" + mode + " -f" + flag)
if mode == "ALL":
	print ("Starting tool in Integrated mode of Upgrade,Healthcheck and Regression tool") 
	os.system("./harness -e " + mail_recp + " -s Testsuites/DCT_Upgrade/upgrade.xml -t" + testbed + " -a" + mode + " -f" + flag)
