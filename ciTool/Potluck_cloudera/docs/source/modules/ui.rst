UI Testing
**********

.. toctree::
   :maxdepth: 2

As of now, Potluck supports `Sikuli <http://www.sikuli.org>`_ based UI automation and follows the below approach:

1. Start a network server on the UI machine (Supported OS: Windows or OSX)
2. The :ref:`ui_server` is usually dormant, and does not do any heroic tasks except when requested by a client
3. The :ref:`ui_client` sends the testcase detail to the Potluck UI server
4. Server launches the sikuli testcase and waits for completion
5. The sikuli testcase uses the :ref:`ui_helpers` to perform the required tasks
6. Meanwhile, the client keeps polling the server for status and waits till the testcase completes

There are three components of Potluck for UI Testing

1. :ref:`ui_server`
2. :ref:`ui_client`
3. :ref:`ui_helpers`

.. _ui_server:

Server
======
.. automodule:: ui_server

.. _ui_client:

Client
======
The Potluck harness acts as a client, which sends appropriate requests to UI server for executing Sikuli based test cases.
It keeps on monitoring the status of the testcase by periodically polling the server

Scripts ending with `.sikuli` are considered as UI Test cases by Potluck

.. _ui_helpers:

Sikuli helpers
==============
Certain helper methods are provided by Potluck to be used in Sikuli scripts

potluck.ui
----------

.. automodule:: potluck.ui
   :members:
