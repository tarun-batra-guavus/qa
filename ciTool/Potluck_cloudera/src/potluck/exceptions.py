"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module provides Potluck specific exceptions
"""

class TcFailedException(Exception):
    """This is the exception raised by :meth:`potluck.reporting.Report.fail` method"""
    pass
