from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import force_text
from home.models import TestsuiteExecution

from multiprocessing import Process
import time
import logging

logger = logging.getLogger(__name__)

class HarnessExecutor(Process):
    def __init__(self, parent, testsuite, *args, **kwargs):
        super(HarnessExecutor, self).__init__(*args, **kwargs)
        self.daemon = True
        self.parent = parent
        self.testsuite = testsuite
        self.name = force_text(testsuite)
        self.testsuite.do_start()   # Marks the testsuite as RUNNING
        
    def run(self):
        self.testsuite.run()
        #self.parent.stdout.write("Completed execution for '%s'" % self.testsuite)
        logger.info("Completed execution for '%s'" % self.testsuite)

class Command(BaseCommand):
    help = 'Starts a new testcase execution'

    def __init__(self, *args, **kwargs):
        self.processes = []
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        try:
            logger.info("Monitoring the execution queue")
            while True:
                testsuite_execution = TestsuiteExecution.objects.filter(state=TestsuiteExecution.ENQUEUED).first()
                if testsuite_execution is None:
                    #logger.info("No execution in queue")
                    time.sleep(5)
                    continue

                logger.info("Next execution in queue: %s" % testsuite_execution)
                # If the testbed is being used by any other execution, then just skip this one
                if TestsuiteExecution.objects.filter(state=TestsuiteExecution.RUNNING, testbed=testsuite_execution.testbed):
                    logger.info("Testbed '%s' is being used by another execution" % testsuite_execution.testbed)
                    time.sleep(5)
                    continue

                # Run the testsuite
                logger.info("Starting the execution for '%s'" % testsuite_execution)
                p = HarnessExecutor(self, testsuite_execution)
                p.start()    # Run the execution in async
                self.processes.append(p) # Keep track of all child processes
        except KeyboardInterrupt:
            logger.info("Interrupted..")
        finally:
            logger.info("Waiting for all the executions to complete")
            for process in self.processes:
                if process.is_alive():
                    logger.info("Waiting for %s" % process)
                    process.join()
