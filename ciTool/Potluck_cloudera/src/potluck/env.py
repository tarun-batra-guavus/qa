"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module houses the environment variables for test script execution.

Example::

    from potluck import env
    print(env.argv.image)

"""

#: Session is used to share data across multiple scripts.
#: `env.session` is a dict that holds the session information.
#:
#: A session is shared for all scripts in a test suite execution. Variables set in
#: the session in one script can be used in later scripts
session = {}

#: An object containing values for all of your options provided on the harness cli
#:
#: e.g. If -i/--image is provided on cli , then ``env.argv.image`` will be the image url
#: supplied by the user, or None if the user did not supply that option
argv = {}

#: List of node aliases specified in the testbed file
node_list = []

#: A dict of nodes present in the testbed file.
#:
#: Keys will be the node alias, and values will be another dict holding the attributes
#: of the node.
#: 
#: Example::
#:
#:     # To get the IP of a node
#:     from potluck import env
#:     insta_ip = env.testbed["Insta1"]["ip"]
testbed = {}

#: An object holding the configuration variables associated with this execution
#: of the testcase.
#:
#: Example::
#:
#:     # If sample.conf config file contains the following entries
#:     [SUITE]
#:     cube_gran = 2
#:
#:     # This config variable can be used in a test script
#:     from potluck import env
#:     Cube_granularity = env.config.cube_gran
from potluck.config import Conf
config = Conf()     # Can be overriden in the harness to parse the config file

def all():
    """Returns a dict of all variables in env. For debugging purposes"""
    all_vars = {}
    for var in dir():
        if not var.startswith("_"):
            all_vars[var] = eval(var)
    return all_vars
