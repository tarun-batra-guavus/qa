########## @package __init__.py
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

IS_SIKULI = False

import sys
if sys.platform.startswith('java'):
    # If in Jython, Apply the python 2.5 compatibility hack for property.setter, property.deleter
    import __builtin__
    if not hasattr(__builtin__.property, "setter"):
        class _property(__builtin__.property):
            __metaclass__ = type
            
            def setter(self, method):
                return property(self.fget, method, self.fdel)
                
            def deleter(self, method):
                return property(self.fget, self.fset, method)
                
            @__builtin__.property
            def __doc__(self):
                """Doc seems not to be set correctly when subclassing"""
                return self.fget.__doc__

        # Monkey Patch the property
        __builtin__.property = _property

# Try to import sikuli
try:
    import sikuli
    IS_SIKULI = True
except ImportError:
    sikuli = None
    IS_SIKULI = False

