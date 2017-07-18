"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module encapsulates the following hadoop related functionalities:

* :class:`Hdfs <potluck.hadoop.hdfs>`
* :class:`Oozie <potluck.hadoop.oozie>`

potluck.hadoop.hdfs
===================

.. automodule:: potluck.hadoop.hdfs
   :members:

potluck.hadoop.oozie
====================

.. automodule:: potluck.hadoop.oozie
   :members:

"""

from .hdfs import Hdfs
from .oozie import Oozie

hdfs = Hdfs()
oozie = Oozie()
