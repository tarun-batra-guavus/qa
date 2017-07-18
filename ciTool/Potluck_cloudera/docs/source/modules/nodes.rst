Nodes
*****

1. :ref:`nodes_module`
2. :ref:`node_apis`
    a) :ref:`node_generic_apis`
    b) :ref:`node_specific_apis`

Potluck follows object oriented approach to manage the nodes

.. _nodes_module:

Generic APIs
============

.. automodule:: potluck.nodes
    :members:

.. _node_apis:

Node APIs
=========
Each Node type has certain APIs available to be used in Test scripts.
A connected node object can use these APIs depending on the type specified in the testbed file.

1) :ref:`node_generic_apis`
2) :ref:`node_specific_apis`

.. _node_generic_apis:

Generic APIs
------------
.. automodule:: potluck.nodes.Node
    :members:

.. _node_specific_apis:

Type Specific APIs
------------------
.. autoclass:: potluck.nodes.CollectorNode.CollectorMixin
    :members:

.. autoclass:: potluck.nodes.NameNode.NameNodeMixin
    :members:

.. autoclass:: potluck.nodes.InstaNode.InstaMixin
    :members:

.. autoclass:: potluck.nodes.DataNode.DataNodeMixin
    :members:

