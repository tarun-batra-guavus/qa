"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

One of the `dream goals` of potluck is to allow people to write scripts in any language of their choice(Perl, Tcl, Shell etc.)

To support this, Potluck follows this approach:

1. Starts a network server on a given port
2. Exposes all the framework APIs via xml-rpc
3. Run the testscript in a child container
4. The child will act as a client and communicates with Potluck via the xml-rpc
5. Potluck can provide client APIs for commonly used languages (like Perl, Ruby etc.)

Thus, these type of testcases are called `remoting tests`, and this module encapsulates the functionality required for running such testcases.
"""
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import operator
import threading
import os
import subprocess

from potluck.logging import logger
from potluck.reporting import report
from settings import MODULES_DIR

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class ServerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ServerThread, self).__init__(*args, **kwargs)
        self._context = {}
        # Create xml-rpc server
        self.server = SimpleXMLRPCServer(("localhost", 9999), requestHandler=RequestHandler)
        self.server.register_introspection_functions()
        self.server.register_instance(self)

    def _dispatch(self, method, params):
        #print("Calling: %r" % method)
        loc, glob, ctx = locals(), globals(), self._context

        if "." in method:
            mod = ""
            # Check the topmost module present in global namespace
            parts = method.split(".")
            for i in xrange(1, len(parts)):
                mod = ".".join(parts[0:i])
                attribute = ".".join(parts[i:])
                # If this module is part of the global namespace
                if mod in glob:
                    mod = glob[mod]
                    try:
                        func = operator.attrgetter(attribute)(mod)
                    except AttributeError:
                        raise AttributeError("'%s' is not an attribute of '%s'" % (attribute, mod))
                    break
                elif mod in ctx:
                    # It can also be an object set in current context
                    mod = ctx[mod]
                    try:
                        func = operator.attrgetter(attribute)(mod)
                    except AttributeError:
                        raise AttributeError("'%s' is not an attribute of '%s'" % (attribute, mod))
                    break
            else:
                raise ValueError("Invalid name: '%s'" % method)
        else:
            # Check the presence of the function to be called
            if "do_%s" % method in dir(self):
                func = getattr(self, "do_" + method)
            elif method in __builtins__:
                func = __builtins__[method]
            elif method in loc:
                func = loc[method]
            elif method in glob:
                func = glob[method]
            elif method in self._context:
                func = self._context[method]
            else:
                #print(globals().keys())
                raise ValueError("Invalid function: '%s'" % method)
        #print("Calling: %r" % func)
        result = func(*params)
        if hasattr(result, "__remote_id__"):
            remote_id = "REMOTE_ID_%s" % result.__remote_id__()
            self._context[remote_id] = result
            ret_val = remote_id
        else:
            ret_val = result
        #print("Returning: %r" % ret_val)
        return ret_val

    def do_import_module(self, module):
        if "." in module:
            top_level_module = module.split(".")[0]
        else:
            top_level_module = module
        globals()[top_level_module] = __import__(module)
        return True

    def run(self):
        # Run the server's main loop
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

class RemoteTest(object):
    def __init__(self, script):
        self.server_thread = ServerThread()
        self.server_thread.daemon = True
        self.script = script

    def getInterpretor(self):
        if self.script.endswith(".pl"):
            cmd = "export PERL5LIB=%s" % os.path.join(MODULES_DIR, "perl")
            return cmd + " && /usr/bin/env perl" + self.getInterpretor() + " " + self.script
        return ""

    def runScript(self):
        cmd = self.getInterpretor() + " " + self.script
        childProcess = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(childProcess.stdout.readline, ""):
            print(line)

        returncode = childProcess.wait()
        if returncode != 0:
            report.fail("Testcase failed")

    def run(self):
        # Run the server thread
        self.server_thread.start()
        logger.info("Started Remoting server")

        # Execute the script in a shell
        self.runScript()

        # Shutdown the server thread
        self.server_thread.shutdown()

