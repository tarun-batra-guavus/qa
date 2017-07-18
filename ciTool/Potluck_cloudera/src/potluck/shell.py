########## @package shell.py
#
# PURPOSE
# -------
# 
# 
# AUTHOR
# ------
# Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>
#
# MODIFICATION HISTORY
# --------------------
# 01-Feb-2013 - sandeep.nanda - Initial Creation
#
##########

import cmd
import traceback
import os
import readline

if 'libedit' in readline.__doc__:
    # For Mac OS
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")

class Shell(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "Potluck> "
        self.intro  = "Welcome to potluck cli.\nYou can execute all the commands which are normally available in a script context"

    def setContext(self, context):
        self._context = context

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print "\n".join(self._hist)

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    def do_runtc(self, args):
        """Runs a testscript"""
        print("Coming soon...")

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        if not hasattr(self, "_context"):
            self._context = {}
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = self._context
        self._globals = self._context

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        stripped_line = line.strip()
        if stripped_line:
            self._hist.append(line)
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            #exec(line) in self._locals, self._globals
            compiled = compile(line, "<string>", "single")
            eval(compiled, self._locals, self._globals)
        except Exception, e:
            print e.__class__, ":", e
