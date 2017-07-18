"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

This module implements the machinery behind the configuration associated with
each test script execution

Normally, you wouldn't need to use this module in the test scripts. An
instance of the config is available in each test script as :obj:`potluck.env.config`

Configuration parameters can be defined in multiple places.

1. A separate config file
2. Within the test suite

.. note:: Historically, The underlying implementation of this module used `ConfigParser` to read the configurations from a file. As this module grew over time, the support to provide configuration from multiple places was added in the framework. Hence as of now, it seems like the complexity added by ConfigParser isn't required. The implementation can be changed to simply using dicts. This change will be at a lower level, and no apparent change will be seen at script level.
"""

import os
import re
import ConfigParser
import xmltodict

import potluck
from potluck.logging import logger
from potluck.mixins import SingletonMixin

class ConfigParamNotFound(AttributeError):
    pass

class Conf(SingletonMixin):
    def __init__(self, config_file=None):
        self._config = ConfigParser.ConfigParser()
        self._config.optionxform = str
        self.contexts = None     # Init the context

        # Read from file if required
        if config_file is not None:
            self.readFromFile(config_file)

    def __str__(self):
        import pprint
        representation = {}
        for section in self._config.sections():
            representation[section] = self._config.items(section)
        return pprint.pformat(representation)

    def readFromFile(self, config_file):
        if not config_file:
            return True

        if not os.path.isfile(config_file):
            logger.error("Config File does not exist: %s" % config_file)
            return False

        try:
            self._config.read(config_file)
            return True
        except Exception, e:
            logger.error(e)
            return False

    @property
    def context(self):
        # Returns the innermost context
        return self._contexts[0]

    @property
    def contexts(self):
        return self._contexts

    @contexts.setter
    def contexts(self, value):
        # `value` should be a tuple
        if not value:
            self._contexts = ("SUITE",)
        else:
            if not hasattr(value, "__iter__"):
                raise ValueError("Config context should be an iterable")
            # Make sure there is always a SUITE context at the end
            self._contexts = value + ("SUITE",)

        # The contexts should be present in the config
        for context in self._contexts:
            if not self._config.has_section(context):
                self._config.add_section(context)


    def set(self, name, value, context=None):
        """Sets the value of a config parameter. If `context` parameter is not given, the local context is used

        :param name: Name of the config parameter
        :param value: Value of the config parameter
        :param context: [Optional] Set the config parameter in this context
        """
        if context is None:
            context = self.context

        if not self._config.has_section(context):
            self._config.add_section(context)

        # If the text is a valid xml with sub-tags, then `value` will be an OrderedDict(or dict) with all the hierarchy
        try:
            xml_str = "<{name}>{value}</{name}>".format(name=name, value=value)
            parsed_dict = xmltodict.parse(xml_str)
        except:
            # Else, `value` will be a string
            return self._config.set(context, name, value)
        else:
            value = parsed_dict[name]
        
        # Else, `value` will be whatever passed in the sub-tags
        self._config.set(context, name, value)
        
    def get(self, name, default=None):
        try:
            return getattr(self, name)
        except ConfigParamNotFound:
            return default

    def itemsDict(self):
        """Returns a dict of {key: value} pairs in the config"""
        items = {}
        # Reverse the context ordering, because we want the inner context to take highest priority
        # E.g. Testcase will override Section will override Suite
        for context in reversed(self.contexts):
            items.update(dict(self._config.items(context)))
        return items

    def items(self):
        """Returns a list of (key, value) pairs in the config"""
        return self.itemsDict().items()

    def __getattr__(self, name):
        ret_val = None
        # Lookup all the contexts one at a time
        #logger.info(self.contexts) 
        for context in self.contexts:
            if self._config.has_option(context, name):
                ret_val = self._config.get(context, name)
                break
        else:
            logger.error(self.contexts)
            # If name is not found in any of the contexts, this is a configuration error
            raise ConfigParamNotFound("'%s' param not found in config." % name)

        ret_val = self._postProcessVariable(ret_val)

        if ret_val:
            # Try to coerce to Integer
            try:
                return int(ret_val)
            except: pass

            # Try to coerce to Float
            try:
                return float(ret_val)
            except: pass

            # Try to coerce to Boolean
            try:
                if re.search("^\s*(true|yes|on)\s*$", ret_val, flags=re.I):
                    return True
                elif re.search("^\s*(false|no|off)\s*$", ret_val, flags=re.I):
                    return False
            except TypeError: pass # For cases where the variable is not string

        # Return as-is
        return ret_val

    def _lookupVariable(self, match):
        var_name = match.group("VAR_NAME")
        if not var_name.startswith("env."):
            full_var_name = "potluck.env." + var_name
        try:
            var_value = eval(full_var_name)
            if callable(var_value):
                var_value = var_value()
            return str(var_value) # Always return a string. It will be coerced later.
        except:
            logger.exception("Invalid variable '%s' found in config" % var_name)
            raise ValueError("Invalid variable '%s' found in config" % var_name)

    def _postProcessVariable(self, val):
        # Check if another variable is requested
        if isinstance(val, basestring):
            return re.sub(r"\$\{\s*(?P<VAR_NAME>\S+)\s*\}", self._lookupVariable, val, flags=re.I)
        elif isinstance(val, dict):
            # Perform post-processing for all keys
            for key, value in val.iteritems():
                val[key] = self._postProcessVariable(value)
            return val

        # If nothing special about this, then return original value
        return val
