Cleanup Actions
***************
.. toctree::
   :maxdepth: 2

While writing test cases, a user can do any kind of changes to the setup without worrying about properly reverting the changes.

Potluck provides the facility to define cleanup actions within the test scripts. These cleanup actions will be called after the execution, irrespective of the state of testcase.

There can be three levels of cleanup actions:

1. Script level cleanup
2. Section level cleanup
3. Suite level cleanup

potluck.cleanup
===============

.. automodule:: potluck.cleanup
    :members:
