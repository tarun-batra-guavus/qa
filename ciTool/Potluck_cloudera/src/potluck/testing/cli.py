"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Encapsulates the functionality required for cli test scripts
"""
import ast

class CliTest(object):
    def __init__(self, script):
        self.script = script

    def run(self):
        """Executes a sikuli based test case."""
        self.printDescription()

        # TODO: Figure out if execfile or __import__ is the better
        # candidate to execute the scripts
        execfile(self.script, locals(), locals())

    def printDescription(self):
        node = ast.parse(''.join(open(self.script)))
        doc_string = ast.get_docstring(node)
        if doc_string:
            print(doc_string)
            print("=" * 80)
