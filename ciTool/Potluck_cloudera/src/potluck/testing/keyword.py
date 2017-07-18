"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Encapsulates the functionality required for keyword based testing
"""
from __future__ import with_statement
from potluck.reporting import report
from potluck.logging import logger
from potluck.nodes import connect

import re
import csv

class KeywordBasedTest(object):
    def __init__(self, script):
        self._nodes = {}
        self._script = script
        self._last_kw = None
        self._last_node = None

    def run(self):
        """Executes a keyword based test case.
        For now, supports csv files
        """
        with open(self._script, "U") as script_fh:
            csv_reader = csv.reader(script_fh)
            csv_reader.next()   # Skip the header

            for index, fields in enumerate(csv_reader, start=2):
                logger.debug("[Line %s] %s" % (index, fields))
                self.exec_keyword(*fields)

    def exec_keyword(self, keyword, *args, **kwargs):
        keyword = keyword.strip().lower()
        if not keyword:
            keyword = self._last_kw
        else:
            self._last_kw = keyword

        method_name = "do_%s" % keyword
        method = getattr(self, method_name)

        if method:
            method(*[x.strip() for x in args])
        else:
            raise ValueError("Invalid Keyword specified: '%s'" % keyword)

    def do_setmode(self, node_alias, targetmode, *args, **kwargs):
        """Executes a command on a device, and checks for the existence of an expected pattern"""
        if not node_alias:
            node = self._last_node
        else:
            if node_alias in self._nodes:
                # If the node is already connected, reuse the existing handle
                node = self._nodes[node_alias]
            else:
                # Else connect the new node
                node = connect(node_alias)

            # Save the last used node and connected node
            self._last_node = self._nodes[node_alias] = node

        logger.info("[%s] Setting Mode '%s'" % (node, targetmode))
        output = node.setMode(targetmode)
        return output

    def do_runcmd(self, node_alias, command, expected_pattern, *args, **kwargs):
        """Executes a command on a device, and checks for the existence of an expected pattern"""
        node_alias = node_alias.strip()

        if not node_alias:
            node = self._last_node
        else:
            if node_alias in self._nodes:
                # If the node is already connected, reuse the existing handle
                node = self._nodes[node_alias]
            else:
                # Else connect the new node
                node = connect(node_alias)

            # Save the last used node and connected node
            self._last_node = self._nodes[node_alias] = node

        logger.info("[%s] Executing command '%s'" % (node, command))
        output = node.sendCmd(command)

        if expected_pattern:
            if not re.search(expected_pattern, output, flags=re.I):
                report.fail("[%s] Pattern '%s' not found in output of cmd '%s'" % (node, expected_pattern, command))
            else:
                logger.info("[%s] Pattern '%s' was found in output" % (node, expected_pattern))

        return output
