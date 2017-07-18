#!/usr/bin/env python
"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Potluck server which listens for Sikuli Based Testcase request from harness.
It listens on `POTLUCK_SERVER_PORT` defined in settings.py

Example usage:

Windows::

    cd Potluck
    server.cmd

Mac/OSX::

    cd Potluck
    ./server.sh

.. note::

    All care has been taken to make this server platform independent. If you find any
    platform related issues, kindly report to the Potluck team
"""

import os
import SocketServer
import pickle
from threading import Thread
from Queue import Queue
import signal
from tempfile import NamedTemporaryFile
import pickle

from potluck.utils import run_cmd, platform
from potluck.logging import logger

from settings import POTLUCK_SERVER_PORT, SCRIPTS_DIR, ROOT_DIR
SERVER_PATH = os.path.abspath(os.path.dirname(__file__))

if platform() == "WIN":
    SIKULI_PATH = os.path.join(SERVER_PATH, "Sikuli", "runScript.cmd")
    JYTHONPATH = "%s;%s" % (SERVER_PATH, SCRIPTS_DIR)
else:
    JYTHONPATH = "%s:%s" % (SERVER_PATH, SCRIPTS_DIR)
    SIKULI_PATH = os.path.join(SERVER_PATH, "Sikuli", "runScript")

# To import Potluck modules

class PotluckRequestHandler(SocketServer.StreamRequestHandler):
    def respond(self, data):
        pickle.dump(data, self.wfile)
        self.wfile.flush()

    def receive(self):
        return pickle.load(self.rfile)

    def handle(self):
        data = self.receive()
        logger.info("Handling request from client: %s" % data)
        # Data should be a dict with following format
        # data = {
        #    "request" : "<ENQUEUE|STATUS>",
        #    "script" : "core/test.sikuli",
        #    "timeout" : 600
        # }
        if data["request"] == "ENQUEUE":
            request_id = self.server.request_id
            self.server.request_status[request_id] = "QUEUED"   # Update the testcase status
            data["request_id"] = request_id     # Fill in the request id
            self.server.tc_request_queue.put(data)  # Submit the testcase request
            self.server.request_id += 1
            ret_val = {
                "request_id" : request_id,
                "success" : True
            }
            logger.info("Testcase queued with request_id: %d" % request_id)
            self.respond(ret_val)
        elif data["request"] == "STATUS":
            request_id = data["request_id"]
            request_status = self.server.request_status.get(request_id, "INVALID_REQUEST_ID")
            ret_val = {
                "success" : True,
                "request_id" : request_id,
                "status" : request_status,
                "logs" : self.server.request_logs.get(request_id, "")
            }
            logger.info("Returning status of request_id %d: %s" % (request_id, request_status))
            self.respond(ret_val)
        elif data["request"] == "SEND_FILE":
            filepath = data["file"]
            # If absolute filepath does not exist, consider it relative to Potluck directory
            if not os.path.exists(filepath):
                filepath = os.path.abspath(os.path.join(ROOT_DIR, filepath))

            # If the path still does not exist, send back an error
            if not os.path.exists(filepath):
                self.wfile.write("ERROR: File does not exist")
            else:
                try:
                    # Open the file to read
                    fileToSend = open(filepath, 'r')
                    logger.info("Sending file '%s' to the client" % filepath)
                    while True:
                        data = fileToSend.readline()
                        if data:
                            self.wfile.write(data)
                        else:
                            break
                    fileToSend.close()
                except Exception as e:
                    self.wfile.write("ERROR: %s" % str(e))
            self.wfile.flush()

class PotluckServer(SocketServer.TCPServer):
    def __init__(self, *args, **kwargs):
        SocketServer.TCPServer.__init__(self, *args, **kwargs)
        self.tc_request_queue = Queue()
        self.tc_response_queue = Queue()
        self.request_status = {}
        self.request_logs = {}
        self.request_id = 1
        self.testcase_executor = TestcaseExecutor(self.tc_request_queue, self.tc_response_queue)
        self.testcase_executor.start()
        self.testcase_updator = Thread(target=self.update_testcase_status)
        self.testcase_updator.start()

    def sigBreak(self, signum, f):
        self.tc_request_queue.put("SHUTDOWN")

    def update_testcase_status(server):
        for data in iter(server.tc_response_queue.get, "SHUTDOWN"):
            # No issue even if this thread blocks
            #data = server.tc_response_queue.get()
            request_id = data.get("request_id")
            if request_id != None:
                request_status = data["status"]
                logger.info("Updating Testcase status for request_id %d: %s" % (request_id, request_status))
                server.request_status[request_id] = request_status
                server.request_logs[request_id] = data.get("logs", "")

class TestcaseExecutor(Thread):
    def __init__(self, request_queue, response_queue, *args, **kwargs):
        super(TestcaseExecutor, self).__init__(*args, **kwargs)
        self.request_queue = request_queue
        self.response_queue = response_queue

    def run(self):
        for data in iter(self.request_queue.get, "SHUTDOWN"):
            #data = self.request_queue.get()
            #logger.debug("Data from parent: %s" % data)
            script = data["script"]
            request_id = data["request_id"]
            ui_url = data["url"]
            config = data.get("config", None)
            ret_val = {
                "request_id" : request_id,
                "status" : "IN_PROGRESS"
            }

            # Inform the parent about progress
            self.response_queue.put(ret_val)
            tc_status, logs = self.execute_tc(script, ui_url, config)
            if tc_status is True:
                ret_val = {
                    "request_id" : request_id,
                    "status" : "PASSED",
                    "logs" : logs
                }
            else:
                ret_val = {
                    "request_id" : request_id,
                    "status" : "FAILED",
                    "logs" : logs,
                }
            self.response_queue.put(ret_val)
        self.shutdown()
    
    def shutdown(self):
        self.response_queue.put("SHUTDOWN")

    def execute_tc(self, script, ui_url, config=None):
        absolute_script_path = os.path.abspath(os.path.join(SCRIPTS_DIR, script))
        if platform() == "WIN":
            cmd = """cmd /C "set JYTHONPATH=%s && %s -r %s -- %s" """ % (JYTHONPATH, SIKULI_PATH, absolute_script_path, ui_url)
        else:
            cmd = "JYTHONPATH=%s %s -r %s -- %s" % (JYTHONPATH, SIKULI_PATH, absolute_script_path, ui_url)

        # Dump the config parameters in a temporary file
        # These will be read by the UI testcase
        if config is not None:
            config_fd = NamedTemporaryFile(delete=False)
            pickle.dump(config, config_fd)
            config_fd.close()
            cmd += " %s" % config_fd.name
        
        logger.debug(cmd)
        output = run_cmd(cmd)
        #print output
        if "TESTCASE PASSED" in output:
            return True, output
        else:
            return False, output

if __name__ == "__main__":
    server_address = ("0.0.0.0", POTLUCK_SERVER_PORT)
    server = PotluckServer(server_address, PotluckRequestHandler)
    logger.info("Listening for connections on %s:%s" % server_address)
    signal.signal(signal.SIGINT, server.sigBreak)
    server.serve_forever()
