"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Implements the client functionality for UI automation.

The client sends appropriate requests to UI server for executing Sikuli based test cases.
It keeps on monitoring the status of the testcase by periodically polling the server
"""

import time
import re
import pickle
import socket
import os
from potluck.reporting import report
from potluck.logging import logger
from potluck import env

from settings import POTLUCK_SERVER_IP, POTLUCK_SERVER_PORT, SCRIPTS_DIR, TMP_DIR

class SikuliTest(object):
    def __init__(self, script, ui_url):
        self.server_ip = POTLUCK_SERVER_IP
        self.server_port = POTLUCK_SERVER_PORT
        self.url = ui_url
        # Since the Server can be on a different machine, so pass the relative path to the server
        self.script = re.sub(SCRIPTS_DIR + "/*", "", script)
        self.poll_interval = 10

    def sendAndReceive(self, data):
        recv_data = ""
        address = (self.server_ip, self.server_port)
        try:
            logger.debug("Establishing connection with UI Server")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(address)
            fd = client_socket.makefile()
            client_socket.close()
        except:
            report.fail("Unable to connect to Potluck UI Server at %s:%s" % address)

        # Send Data To server
        pickle.dump(data, fd)
        fd.flush()

        # Receive data from server
        recv_data = pickle.load(fd)
        fd.close()
        return recv_data

    def receiveFile(self, source_file, dest_file):
        recv_data = ""
        address = (self.server_ip, self.server_port)
        try:
            logger.debug("Establishing connection with UI Server")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(address)
            fd = client_socket.makefile()
            client_socket.close()
        except:
            report.fail("Unable to connect to Potluck UI Server at %s:%s" % address)

        logger.info("Trying to receive file from UI server. Source: '%s', Dest: '%s'" % (source_file, dest_file))
        # Data to be sent to the server
        data = {
            "request" : "SEND_FILE",
            "file" : source_file
        }
        
        # Send Data To server
        pickle.dump(data, fd)
        fd.flush()

        # Receive file from server and
        # Write the data to the dest file
        fname = open(dest_file, 'w')
        firstline = True
        while True:
            data = fd.readline()
            if data:
                if firstline is True and data.startswith("ERROR"):
                    logger.error(data)
                else:
                    fname.write(data)
            else:
                break
            firstline = False

        # Close the file descriptors
        fname.close()
        fd.close()
        return True

    def run(self):
        """Executes a sikuli based test case."""

        # Data to send to the server
        data = {
            "request" : "ENQUEUE",
            "script" : self.script,
            "url"    : self.url,
            "config" : env.config.itemsDict(),
            "timeout" : 600     # None of the test case should take more than 10 minutes to complete
        }

        logger.info("Submitting testcase to UI Server")
        data = self.sendAndReceive(data)
        request_id  = data["request_id"]
        logger.info("Testcase submitted with ID: %s" % request_id)
        # Wait here for completion of the test case
        while True:
            # Poll after every 60 secs
            logger.info("Waiting for %d secs" % self.poll_interval)
            time.sleep(self.poll_interval)

            logger.info("Getting Testcase status from Potluck Server")
            data = self.sendAndReceive({
                "request" : "STATUS",
                "request_id" : request_id
            })

            if data.get("success", False):
                request_status = data["status"]
                tc_logs = data.get("logs")
                logger.debug("Testcase Execution Status: %s" % request_status)

                if tc_logs:
                    logger.info(tc_logs)

                if request_status == "PASSED":
                    logger.info("Sikuli Testcase passed")
                elif request_status == "FAILED":
                    try:
                        screenshot_match = re.search("Screenshot placed at:\s*(?P<SCREENSHOT>.+)", tc_logs, flags=re.I)
                        if screenshot_match:
                            remote_screenshot_path = screenshot_match.group("SCREENSHOT")
                            screenshot_filename = remote_screenshot_path.split("\\")[-1]
                            local_screenshot_path = os.path.join(TMP_DIR, screenshot_filename)  # Local path should be in tmp directory
                            self.receiveFile(remote_screenshot_path, local_screenshot_path)
                            logger.info("Local screenshot located at %s" % local_screenshot_path)
                    except Exception, e:
                        # Nothing so important to raise an alarm
                        logger.warning("Unable to copy screenshot from remote machine")
                        logger.warning(str(e))
    
                    report.fail("Sikuli Testcase Failed")
                elif request_status in ["QUEUED", "IN_PROGRESS"]:
                    continue
            break   # Break if-not-handled, to avoid infinite loops when this code becomes large
