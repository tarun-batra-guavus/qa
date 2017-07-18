"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides reporting methods.

In a test script, you would need to use this module whenever
there is a need to fail a test case

Example Usage::

    from potluck.reporting import report

    report.fail("Something wrong happened")
"""
from __future__ import with_statement

import sys
from termcolor import colored
import re
from potluck.logging import Logger
from potluck.utils import sendEmail
from potluck.exceptions import TcFailedException
from potluck.mixins import SingletonMixin

# Always display logs on screen
logger = Logger(sys.stderr)

# Singleton Report class
class Report(SingletonMixin):
    """This is a singleton class which provides the methods used
    to report testcase status in a test case.

    Normally, you wouldn't need to create an instance yourself.
    An instance of this class (:obj:`.report`) is already provided by the framework.

    There are some undocumented methods provided by this class, which are internally
    used by the framework. View the source to get more information.
    """
    def __init__(self):
        self.WEB_URL = ""
        self.SUITE = ""
        self.TESTBED = ""
        self.BUILD = ""
        self.fail_count = 0
        self.pass_count = 0
        self.skip_count = 0
        self.testcase_status = []
        self.total_count = 0
        self.latest_tc_status = ""
        self.latest_fail_message = ""
        self.reset_tc()

    @property
    def executed_count(self):
        return self.pass_count + self.fail_count

    @property
    def pass_percent(self):
        return (self.pass_count * 100) / self.total_count

    def reset_tc(self):
        self.error_count = 0
        self.tc_failed = False

    def error(self, message):
        # This method is called from logger.error
        # Not storing error message for now, just increment the counter
        self.error_count += 1

    def fail(self, message, proceed=False):
        """Mark a Testcase as FAILED.

        The current script execution aborts when a testcase fails

        If `proceed` is True, the testcase execution is not aborted and
        the script continues to run
        """
        print("[FAILED] " + message)    # Override the logger to print the log in the script logs
        self.tc_failed = True
        self.latest_fail_message = message
        if not proceed:
            raise TcFailedException

    def pass_or_fail(self, tc):
        if self.tc_failed:
            # If the test has already failed elsewhere (i.e. fail_and_proceed is used)
            self.fail_tc(tc)
        else:
            self.pass_tc(tc)

    def pass_tc(self, tc):
        self.pass_count += 1
        self.latest_tc_status = "PASSED"
        if self.error_count > 0:
            status = "PASSED WITH ERRORS"
            color = "magenta"
        else:
            status = "PASSED"
            color = "green"
        self.testcase_status.append({
            "tc" : tc,
            "status" : status
        })
        logger.info("%s : %s" % (tc["id"], colored(status, color)))
        self.reset_tc()

    def fail_tc(self, tc):
        self.fail_count += 1
        self.latest_tc_status = "FAILED"
        self.testcase_status.append({
            "tc" : tc,
            "status" : "FAILED",
            "remarks" : self.latest_fail_message
        })
        logger.info("%s : %s" % (tc["id"], colored("FAILED", "red")))
        self.reset_tc()

    def skip_tc(self, tc):
        self.skip_count += 1
        self.latest_tc_status = "SKIPPED"
        self.testcase_status.append({
            "tc" : tc,
            "status" : "SKIPPED",
        })
        logger.info("%s : %s" % (tc["id"], colored("SKIPPED", "gray")))
        self.reset_tc()

    def print_report(self, filename, mail_to=None,build=""):

        # Get report for each testcase
        report_str, report_str_html = self.tc_status_report()

        report_str += "\nDetailed Logs can be viewed at: %s\n" % self.WEB_URL
        #report_str_html += "<br />Detailed Logs can be viewed at: <a href='%s'>Potluck Logs</a>" % self.WEB_URL

        # Display the report on stdout
        logger.info(report_str)
        project_name = self.TESTBED.split("-")[0]
	print self.TESTBED
        setup_name = self.TESTBED.split("-")[1]
        
        mail_body = "Potluck Execution report\n"
        mail_body += "************************\n\n"

        
        #subject = "Test Execution report"
        
        subject = "Continuous Deployment:" + project_name + ":" + self.SUITE.upper()
        if self.BUILD:
            subject = "Test Execution report for %s" % self.BUILD

        if build:
            mail_body += "Build : %s\n" % build
        else:
            mail_body += "Build : %s\n" % self.BUILD or "N/A"
        mail_body += "TestSuite : %s\n" % self.SUITE
        mail_body += "TestBed : %s\n" % self.TESTBED
        mail_body += "\nSummary\n"
        mail_body += report_str

        mail_body_html = """
            <html>
            <head>
                <style>
                    body {
                        font: normal 12px verdana,sans-serif;
                    }
                    table {
                        border-collapse: collapse;
                        font: normal 12px verdana,sans-serif;
                    }
                    table, td {
                        border: 1px solid #FF8300;
                    }
                    th {
                        color: #FFF;
                        font-weight: bold;
                        background-color: #FF8300;
                    }
                    th.section {
                        background-color: #25373E;
                    }
                </style>
            </head>
            <body>
            <h1>Potluck Execution report</h1>
            <table style='width:400px'>
                <tr>
                    <th style="width:20%%">Build</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th>TestSuite</th>
                    <td>%s</td>
                </tr>
                <tr>
                    <th>TestBed</th>
                    <td>%s</td>
                </tr>
            </table>
            <br/>
            %s
            <br/>
            <br/>
            Thanks,<br/>
            Potluck Team
            </body></html>
            """ % (build or self.BUILD or "N/A", self.SUITE, self.TESTBED, report_str_html)

        txt_file = filename + ".txt"
        logger.info("Saving report at: %s" % txt_file)
        with open(txt_file, "w") as report_file:
            report_file.write(mail_body)

        html_file = filename + ".html"
        logger.info("Saving html report at: %s" % html_file)
        with open(html_file, "w") as report_file:
            report_file.write(mail_body_html)

        if mail_to:
            mail_body += "\n\nThanks,\nPotluck Team"
            try:
                sendEmail(mail_to.split(","), subject, mail_body, body_html=mail_body_html)
            except Exception, e:
                logger.warn("Error while sending report email")
                logger.warn(e)

    def tc_status_report(self):
        report_str = ""
        report_str_html = ""

        test_cases_str = "Total Cases: %d" % self.total_count
        exec_cases_str = "Executed: %d" % self.executed_count
        pass_percent_str = "Pass Percent: %d%%" % self.pass_percent

        # Text Report
        report_str += "#"*60 + "\n"
        report_str += "%-27s # %27s  #\n" % ("", "")
        report_str += "%-27s # %27s  #\n" % (test_cases_str, "")
        report_str += "%-27s # %27s  #\n" % (exec_cases_str, pass_percent_str)
        report_str += "%-27s # %27s  #\n" % ("Passed: %d" % self.pass_count, "")
        report_str += "%-27s # %27s  #\n" % ("Failed: %d" % self.fail_count, "")
        report_str += "%-27s # %27s  #\n" % ("", "")
        report_str += "#"*60 + "\n"
        report_str += "Executed testcases\n"
        report_str += "="*20 + "\n"

        # HTML Report
        report_str_html += "<table style='width:400px'>"
        report_str_html += "<tr><th colspan=2>Summary</th></tr>"
        report_str_html += "<tr><td>Total Cases</td><td>%s</td></tr>" % self.total_count
        report_str_html += "<tr><td>Executed</td><td>%s</td></tr>" % self.executed_count
        report_str_html += "<tr><td>Pass Percent</td><td>%s%%</td></tr>" % self.pass_percent
        report_str_html += "<tr><td>Passed</td><td>%s</td></tr>" % self.pass_count
        report_str_html += "<tr><td>Failed</td><td>%s</td></tr>" % self.fail_count
        report_str_html += "</table><br/>"
        report_str_html += "<h3>Testcase details</h3>"
        report_str_html += "<table style='width:750px'>"
        last_section_name = None
        counter = 0
        for tc_status in self.testcase_status:
            tc = tc_status["tc"]
            status = tc_status["status"]
            remarks = tc_status.get("remarks")
            section_name = tc["section"]["name"]
            logs_url = self.WEB_URL + "/" + tc["logfile_name"]
            tc_description = tc.get("description") or tc["id"]
            counter += 1
            if "PASSED WITH ERRORS" in status:
                ansi_color = color = "magenta"
            elif "PASSED" in status:
                ansi_color = color = "green"
            elif "FAILED" in status:
                ansi_color = color = "red"
            else:
                ansi_color = color = "gray"

            if section_name != last_section_name:
                if last_section_name != None:
                    report_str_html += "<tr><td colspan=4>&nbsp;</td></tr>"     # Keep an empty row between sections
                report_str_html += "<tr><th class=section colspan=4>%s</th></tr>" % section_name
                report_str_html += "<tr><th>Sr No.</th><th>Testcase</th><th>Status</th><th style='max-width:200px'>Failure Reason</th></tr>"
                report_str += "-" * (len(section_name) + 9) + "\n"
                report_str += "SECTION: %s\n" % section_name
                report_str += "-" * (len(section_name) + 9) + "\n"
            last_section_name = section_name

            if len(tc_description) <= 45:
                format_str = "%2d. %-45s : %10s %s\n"
            elif len(tc_description) <= 50:
                format_str = "%2d. %-50s : %10s %s\n"
            elif len(tc_description) <= 55:
                format_str = "%2d. %-55s : %10s %s\n"
            else:
                format_str = "%2d. %-60s : %10s %s\n"

            report_str += format_str % (counter, tc_description, colored(status, ansi_color), "[%s]" % colored(remarks, ansi_color) if remarks else "")
            report_str_html += "<tr><td>%s</td><td><a href='%s'>%s</a></td><td style='color: %s'>%s</td><td style='max-width:100px'>%s</td></tr>\n" % \
                               (counter, logs_url, tc["id"], color, status, remarks)
        report_str += "#"*60 + "\n"
        report_str_html += "</table>"

        return report_str, report_str_html

#: An instance of the :obj:`Report` class, to be used for reporting the status of the testcase
#:
#: Example Usage::
#:
#:    from potluck.reporting import report
#:
#:    report.fail("Something wrong happened")
report = Report()
