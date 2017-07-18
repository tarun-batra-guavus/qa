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

import os
import re
import traceback
from datetime import datetime
import optparse

now = datetime.now
log_dir = "/var/www/html/Potluck_cloudera/useroutput/Test_Reports"

from potluck.logging import Logger, logger as script_logger
from potluck.reporting import report
from potluck.exceptions import TcFailedException
from potluck.testing import run_script
from potluck.cleanup import cleanup
from potluck import utils
from potluck import env
from potluck import nodes

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

# Defaults
MailTo = None
ConfigFile = None

# Constants
IS_WEB_EXECUTION = False

# Note down the start time
start_time = now()

# Various timestamps needed further in the harness
start_timestamp = start_time.strftime("%Y%m%d%H%M%S")
start_date_str = start_time.strftime("%Y-%m-%d")
start_time_str = start_time.strftime("%H:%M:%S")

epoch_folder = log_dir + "/" + start_date_str + "_" + start_time_str
os.makedirs(epoch_folder)
for file in os.listdir(log_dir):
        if "diff" in file:
                print "file to be moved is :",file
                os.rename(file,epoch_folder)


# Parse command line options
parser = optparse.OptionParser()
parser.add_option("-t", "--testbed", dest="testbed",
                  help="Testbed to use for testing [MANDATORY]")
parser.add_option("-s", "--suite", dest="suite",
                  help="Execute the given suite of testcases")
parser.add_option("-r", "--script", dest="script",
                  help="Run a single script file [Cannot be used with --suite]]")
parser.add_option("-i", "--image", dest="image",
                  help="Image URL")
parser.add_option("-m", "--mail_to", dest="mail_to",
                  help="Comma Separated email ids of people whom to send the report")
parser.add_option("-c", "--config", dest="config_file",
                  help="Path to the config file to be used for this test execution")
parser.add_option("-u", "--ui_url", dest="ui_url",
                  help="UI url")
parser.add_option("--sections", dest="sections",
                  help="Run only these sections from the suite. Case-Insensitive comma separated values")
parser.add_option("-d", "--dbid", dest="dbid",
                  help=optparse.SUPPRESS_HELP)
parser.add_option("--shell", action="store_true", dest="shell",
                  help=optparse.SUPPRESS_HELP)

(options, args) = parser.parse_args()

harness_logger = Logger(sys.stderr)

if options.dbid is not None:
    IS_WEB_EXECUTION = True
    # Setup django to use its utilities
    os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'
    import django
    django.setup()
    from django.utils.timezone import now

    # Bypass all other cli arguments
    start_time = now()

    from home.models import TestsuiteExecution, TestcaseExecution
    try:
        testsuite_obj = TestsuiteExecution.objects.get(pk=options.dbid)
        options.suite = str(testsuite_obj.suite)
	print options.suite
        options.testbed = str(testsuite_obj.testbed)
        options.image = str(testsuite_obj.build.image_path)
        options.ui_url = str(testsuite_obj.ui_url)
        options.mail_to = str(testsuite_obj.user.username)
    except TestsuiteExecution.DoesNotExist:
        harness_logger.error("Testsuite ID '%s' does not exist in database" % options.dbid)
        sys.exit(1)
else:
    if not options.suite and not options.shell and not options.script:
        harness_logger.error("Suite or Script is a mandatory argument. Use 'harness.py --help'")
        parser.print_help()
        exit(1)

    if options.suite and options.script:
        harness_logger.error("Suite and Script cannot be passed together. Use only one of 'em.")
        parser.print_help()
        exit(1)

    if not options.testbed:
        harness_logger.error("Testbed is a mandatory argument. Use 'harness.py --help'")
        parser.print_help()
        exit(1)

if options.sections:
    options.sections = map(lambda s: s.strip(), options.sections.lower().split(","))

# Parse the testbed file
tb_name = os.path.split(options.testbed)[-1]
nodes.testbed = utils.parse_testbed(options.testbed)
print "nodes.testbed is:", nodes.testbed
if not nodes.testbed:
    harness_logger.error("Testbed file does not exist '%s'" % options.testbed)
    sys.exit(1)

nodes.alias_list = nodes.testbed.keys()

# Set the initial env for script executions
env.argv = options
env.node_list = nodes.alias_list
env.testbed = nodes.testbed

# Drop in shell if that is requested
if options.shell:
    from potluck.shell import Shell
    Shell().cmdloop()
    exit(0)

if options.script:
    global_section = {
        "testcases" : [],
        "name" : "Global"
    }
    suite = {
        "name" : "",
        "sections" : []
    }
    # Make a TC id by replacing all the slashes with hyphens
    tc_id = utils.generate_testcase_id(options.script)
    script_prefix, ext = os.path.splitext(options.script)

    suite["name"] = os.path.split(script_prefix)[-1]   # To be used for reporting

    if os.path.exists(options.script):
        # If absolute path is passed, use it
        script_file = os.path.abspath(options.script)
    else:
        script_file = os.path.join(SCRIPTS_DIR, options.script)

    if os.path.isfile(script_file):
        global_section["testcases"].append({"script" : script_file, "rule" : None, "id" : tc_id, "description" : None})
        suite["sections"] = [global_section]
    else:
        harness_logger.error("Script does not exist %r, or is not a regular file" % script_file)
        exit(1)
else:
    suite = utils.parse_suite_xml(options.suite)

    if suite == None:
        harness_logger.error("Unable to parse Test suite")
        exit(1)
    else:
        sections = suite.get("sections", [])
        MailTo = suite.get("mail_to")
        ConfigFile = suite.get("config_file")
        suite_ui_url = suite.get("ui_url")
        # If UI Url is not passed via CLI, take from config file
        if suite_ui_url and not options.ui_url:
            options.ui_url = suite_ui_url

harness_logger.info("Execution for suite '%s' started on testbed '%s' at: %s" % (suite["name"], options.testbed, start_time))

# If there is even one UI testcase, validate that we need the Ui URL
is_ui_test = utils.has_ui_testcases(suite)
if is_ui_test:
    if not options.ui_url:
        harness_logger.error("There is some UI Testcases in the suite, but no UI Url is passed")
        exit(1)
    else:
        harness_logger.info("UI Url: %s" % options.ui_url)

# Params specified on cli will take preference
if options.mail_to:
    MailTo = options.mail_to
if options.config_file:
    ConfigFile = options.config_file

# If Config file is passed, read it
if ConfigFile is not None:
    env.config.readFromFile(ConfigFile)

# Create a new log directory for this execution
suite_name = suite["name"].replace(".xml", "")
logdir_name = "%s.%s" % (suite_name, start_time_str)
relative_logdir_path = os.path.join(tb_name, start_date_str, logdir_name)
logdir_path = os.path.join(LOGS_DIR, relative_logdir_path)
report_file = os.path.join(logdir_path, "report")
os.makedirs(logdir_path)

# Fill in parameters required by reporting subsystem
report.WEB_URL = "http://%s/Potluck_backup/logs/%s" % (MACHINE_IP, relative_logdir_path)
report.SUITE = suite_name
report.TESTBED = tb_name
if options.image:
    report.BUILD = options.image.split("/")[-1]
harness_logger("Logs will be stored at: %s" % logdir_path)
harness_logger("Logs can be viewed through a web browser at : %s" % report.WEB_URL)

if IS_WEB_EXECUTION:
    # Store relative path, so logs dir can change at any time
    testsuite_obj.logs_path = relative_logdir_path
    testsuite_obj.do_start(start_time)

total_testcases = sum(len(section["testcases"]) for section in suite["sections"])
report.total_count = total_testcases
index = 0
abort_execution = False
try:
    # If a user has asked to execute only a particular section
    if options.sections:
        harness_logger.info("Running only these sections: %r" % options.sections)
        sections_to_run = filter(lambda sec: sec["name"].lower() in options.sections, suite["sections"])
    else:
        sections_to_run = suite["sections"]

    for section in sections_to_run:
        try:
            harness_logger.info("\n===============================")
            harness_logger.info("SECTION: %s" % section["name"])
            harness_logger.info("===============================")
            skip_section = False

            # Start executing testcases
            for tc in section["testcases"]:
                index += 1
                report.reset_tc()
                script = tc["script"]
                rule = tc["rule"]
                tc_id = tc["id"]
                description = tc.get("description", None)
                tc["section"] = section
                script_start_time = now()
                script_start_timestamp = script_start_time.strftime("%H%M%S")

                # Open a logfile for this script
                #script_logfile_name = "%s.%s.log" % (re.sub(r"\s", "_", tc_id), script_start_timestamp)
                script_logfile_name = "%s.%s.log" % (os.path.splitext(os.path.split(script)[-1])[0], script_start_timestamp)
                script_logfile_path = os.path.join(logdir_path, script_logfile_name)
                rel_script_logfile_path = os.path.join(relative_logdir_path, script_logfile_name)
                tc["logfile_name"] = script_logfile_name
                tc["logfile_path"] = script_logfile_path

                harness_logger.info("\nExecuting (%d/%d): %s" % (index, total_testcases, description or tc_id))
                harness_logger.info("Logfile: %s" % script_logfile_path)

                # Set the configuration mentioned in the testsuite
                env.config.contexts = (tc_id, os.path.split(script)[-1], "SECTION_%s" % section["name"])

                with open(script_logfile_path, "w") as script_logfile:
                    stdout = sys.stdout
                    sys.stdout = utils.processed_stream(script_logfile)

                    try:
                        # Update the DB for web executions
                        if IS_WEB_EXECUTION:
                            testcase_obj = testsuite_obj.testcaseexecution_set.create(script=script,
                                                                              tc_id=tc_id,
                                                                              started_at=script_start_time,
                                                                              logs_path=rel_script_logfile_path,
                                                                              section=section["name"],
                                                                              state=TestcaseExecution.State.RUNNING)

                        # Check if we need to skip all the testcases
                        if skip_section:
                            harness_logger.notice("Testcase Skipped")
                            sys.stdout = stdout
                            report.skip_tc(tc)
                            if IS_WEB_EXECUTION:
                                testcase_obj.status = TestcaseExecution.Status.SKIPPED
                                testcase_obj.state = TestcaseExecution.State.NOT_RUN
                        else:
                            # Form the parameters required to be sent to the script
                            args = []
                            if options.ui_url:
                                args.append(options.ui_url)

                            # Run the Test script
                            run_script(script, *args)

                            # Decide pass or fail
                            report.pass_or_fail(tc)
                    except TcFailedException:
                        report.fail_tc(tc)
                    except Exception as e:
                        tb = traceback.format_exc()
                        # Log the traceback in script logs as well as on screen
                        script_logger.error(tb)
                        harness_logger.error(tb)
                        exc_str = traceback.format_exception_only(*sys.exc_info()[0:2])[0]
                        report.latest_fail_message = exc_str.strip()
                        report.fail_tc(tc)
                    finally:
                        # Run script level cleanup actions
                        harness_logger.info("Running Script cleanup actions. DO NOT PRESS CTRL+C")
                        cleanup.doScriptCleanup()
                        sys.stdout = stdout
                        if IS_WEB_EXECUTION:
                            if testcase_obj.state != TestcaseExecution.State.NOT_RUN:
                                if report.latest_tc_status == "FAILED":
                                    testcase_obj.status = TestcaseExecution.Status.FAILED
                                    testcase_obj.remarks = report.latest_fail_message
                                else:
                                    testcase_obj.status = TestcaseExecution.Status.PASSED
                            testcase_obj.do_complete()

                # Process the rules if the testcase has failed
                if report.latest_tc_status == "FAILED":
                    if not rule:
                        # Don't do anything if a rule is not defined
                        pass
                    elif rule == "ABORT":
                        harness_logger.notice("Testcase FAILED. Aborting Execution..")
                        abort_execution = True
                        break
                    elif rule == "ABORT_SECTION":
                        harness_logger.notice("Testcase FAILED. Aborting Section..")
                        skip_section = True
                    else:
                        harness_logger.error("Invalid rule: %s" % rule)
        finally:
            # Run section level cleanup actions
            harness_logger.info("\nRunning section %s's cleanup actions. DO NOT PRESS CTRL+C" % section["name"])
            section_cleanup_log_path = os.path.join(logdir_path, "section_%s.cleanup" % section["name"])
            with open(section_cleanup_log_path, "w") as logfile:
                stdout = sys.stdout
                sys.stdout = utils.processed_stream(logfile)
                cleanup.doSectionCleanup()
                sys.stdout = stdout

        # Abort the whole execution
        if abort_execution:
            break
finally:
    if IS_WEB_EXECUTION:
        testsuite_obj.do_complete()

    # Run suite level cleanup actions
    harness_logger.info("Running suite cleanup actions. DO NOT PRESS CTRL+C")
    suite_cleanup_log_path = os.path.join(logdir_path, "suite.cleanup")

    with open(suite_cleanup_log_path, "w") as logfile:
        stdout = sys.stdout
        sys.stdout = utils.processed_stream(logfile)
        cleanup.doSuiteCleanup()
        sys.stdout = stdout

    report.print_report(report_file, MailTo)
    
