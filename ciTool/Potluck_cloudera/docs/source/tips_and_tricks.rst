Tips & Tricks
*************

Installation
============

Potluck has been included in the `qa` git repository.

If you just want to browse the code, you can see it in any browser. Here is a `link to the source <https://guavus-gurgaon.guavus.com/gitweb?p=qa.git;a=tree;f=Potluck;h=73ccd3c9d7e113512f1739d4125fdcaac8928543;hb=HEAD>`_.

Installation of Potluck on your own machine is pretty simple, and does not require any 3rd party library. All the dependencies have been included along with the base code.

Execute the following commands to get the potluck code::

    mkdir ~/repos
    cd ~/repos

    # Turn off SSL verify
    git config --global http.sslverify false

    # Clone the repo (Use your git credentials)
    git clone https://guavus-gurgaon.guavus.com/gitrepos/qa.git

    # Potluck is now installed in ~/repos/qa/Potluck
    cd qa/Potluck

Execution
=========
Execute ``./harness -h`` to get help on all the available options

Command line Usage::

    cd Potluck
    ./harness --suite=SUITE --testbed=TESTBED --image=IMAGE

Mandatory Arguments
-------------------
.. cmdoption:: -s <suite>, --suite=<suite>

Suite is an xml file having the information of the testcases to execute

Please refer to ``Testsuites`` directory for sample suite information.
``Testsuites`` folder should have a human readable file called <filename>.xml , the content of this file should be a list of test scripts wherein each script corresponds to a single test case.

.. cmdoption:: -t <testbed file>, --testbed=<testbed file>

Please refer to ``Testbeds`` directory for sample test bed information.
``Testbeds`` folder should have a human redable file containing complete information about your test setup. like machine type, machine IP, password etc. These feilds have to be tab seperated.

Optional Arguments
------------------
.. cmdoption:: -i <image_url>, --image=<image_url>

This argument should be used only in case tester want to upgrade the test bed with new image.
This image can be in form of http url or an scp command as expected by TM console. Please refer to ``image fetch ?`` at config prompt for more details.
Please note that while using upgrade potluck will upgrade all nodes present in your testbed.

.. cmdoption:: -u <ui url>, --ui_url=<ui url>

THe URL of the ui. This is required if the test suite contains one or more `.sikuli` testcases

.. cmdoption:: -m <mail_to>, --mail_to=<mail_to>

After the completion of test execution, an email will be sent to the user ids mentioned here.

Multiple email ids can be separated by comma(,). Trailing @guavus.com an be left out

Testcase Primer
===============

Env Variables
-------------
A script can use certain variables provided by the framework.

More details in :mod:`potluck.env` module

**env.argv** :  

All the arguments passed on the cli::

    # To access the `image` url passed on the cli
    from potluck import env
    my_image = env.argv.image


**env.node_list**

List of node aliases specified in the testbed file


**env.testbed**  

A dict of nodes present in the testbed file.  
Keys will be the node alias, and values will be another dict having the node attributes ::

    # To get the IP of a node
    from potluck import env
    insta_ip = env.testbed["Insta1"]["ip"]

**env.config**  

Configuration associated with this execution of the testcase

**env.session**  

Session to be used if you need to share data across testcases ::

    # Script1.py
    # Set a session variable
    from potluck import env
    env.session["MyVariable"] = 23

    # Script2.py
    # Use the session variable that was set in previous script
    from potluck import env
    from potluck.logging import logger
    my_variable = env.session["MyVariable"]
    logger.info(my_variable)    # Will output 23


Failing a testcase
------------------
To signify a failure in the testcase, use the :meth:`.reporting.Report.fail` method.  
Calling this method will abort the execution of the testcase

Example::

    from potluck.reporting import report

    report.fail("Reason for failure")


If you need to signify failure but continue the execution of the testcase, call the `fail` method as following::

    from potluck.reporting import report

    report.fail("Testcase will Fail, but execution will continue", proceed=True)

