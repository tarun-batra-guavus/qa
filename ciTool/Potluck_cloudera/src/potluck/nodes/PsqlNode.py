"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Implements Psql specific APIs
"""

from Node import Node
from potluck.logging import logger

import re
import time

class PsqlMixin(object):
    def runPsqlQuery(self, cmd, db=None, ignoreErrors=False):
        """Executes a given psql query on this insta machine"""
        if not cmd.endswith(";"):
            cmd += ";"
        psql_cmd = """psql -A -t -U postgres -c "%s" """ % re.sub('"', r'\"', cmd)
        if db is not None:
            psql_cmd += " -d %s" % db

        self.pushMode("shell")
        output = self.sendCmd(psql_cmd)
        self.popMode()

        if re.search("syntax error", output, re.I):
            logger.error("Syntax error in psql command")
            output = None
        elif ignoreErrors is False and re.search("(FATAL|ERROR):", output, re.I):
            logger.error("Error in executing psql command")
            output = None

        return output

    def dropPsqlDatabase(self, db_name):
        """Drops a given psql database"""
        logger.info("Killing any processes that are using database '%s'" % db_name)
        cmd = "SELECT pid from pg_stat_activity where datname='%s'" % db_name
        pids = self.runPsqlQuery(cmd)
        for pid in pids.split("\n"):
            # Skip if pid is not valid
            try:
                pid = int(pid.strip())
            except: continue

            # Terminate the process
            self.runPsqlQuery("SELECT pg_terminate_backend(%d)" % pid)

        logger.info("Dropping psql database '%s'" % db_name)
        cmd = "DROP DATABASE IF EXISTS %s" % db_name
        return self.runPsqlQuery(cmd)
        
    def createPsqlDatabase(self, db_name, drop=False):
        """Creates a given psql database"""
        if drop is True:
            self.dropPsqlDatabase(db_name)

        logger.info("Creating psql database '%s'" % db_name)
        cmd = "CREATE DATABASE %s" % db_name
        output = self.runPsqlQuery(cmd, ignoreErrors=True)

        # Check for errors in output
        if "already exists" in output:
            logger.notice("DB '%s' already existed in postgres. Not doing anything.." % db_name)
        elif re.search("(FATAL|ERROR):", output, re.I):
            logger.error("Error in executing psql command")
            return None
        return output
        
class PsqlNode(PsqlMixin, Node):
    pass

