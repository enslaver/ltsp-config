# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 18:51:49 2013

The purpose of this module is to provide a validation layer for the variables
the user has set.  Each of these variables should, at the very least, be of
a particular type, some in a particular range.

Data type names are exported to the 'configuration' module via the
'get_data_types' method.  This way, we can ensure that the configured data
type in the configuration file has a corresponding DataType here, and it can
be checked against that.  If the DataType fails to instantiate, it should riase
a ValueError, which contains a (potentially useful) message.

The Validator class, at present, only has one method -- validate, and one
data object, a dict of DataType.name: DataType.  The validate method should
be called with a type name and the value of the field.

This module has no external dependencies outside of the python standard lib.
To get a list of available data types, do:
import data_validation
data_validation.get_data_types()

## Adding a data type
To create a new data type to use in the config file, create a class here.
The class should have a member "name", which is the name to use in the config
file.  The __init__ of the class should take one argument, "value", and
__init__ should raise a ValueError if the value does not fit the criteria.
"""

import os
import re
from datetime import datetime
from glob import glob


class DataType(object):
    # 'name' should be one of the valid DATA_TYPES, except for this base class.
    name = None

    def __init__(self):
        if self.name is None:
            raise NotImplementedError("'name' class variable not set.")


class String(DataType):
    name = 'string'

    def __init__(self, value):
        if not isinstance(value, str):
            raise TypeError('"{}" is not a string.'.format(value))


class Integer(DataType):
    name = 'integer'

    def __init__(self, value):
        int(value)


class Boolean(DataType):
    name = 'boolean'
    _valid_values = {'true', 'false', '0', '1', 0, 1, True, False, 'yes', 'no'}

    def __init__(self, value):
        if isinstance(value, str):
            value = value.lower()
        if not value in self._valid_values:
            msg = '"{}" is not a recognized boolean value.'
            raise ValueError(msg.format(value))


class IpAddress(DataType):
    name = 'ip address'
    _regexp = (r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
               r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
    _valid_ip = re.compile(_regexp)

    def __init__(self, value):
        if not self._valid_ip.match(value):
            msg = '"{}" is not recognized as a valid IP address.'
            raise ValueError(msg.format(value))


class Port(DataType):
    name = 'port'

    def __init__(self, value):
        if not 0 < int(value) <= 65535:
            raise ValueError("Port %s is out of range 1-65535" % value)


class FilePath(DataType):
    """Really, any string will work and be considered a valid file path.
    Linux filepaths can even contain newline characters.
    It may be a good idea to put in some common-sense restrictions here --
    however, for now, if it's a string, it's fine.
    Examples of things that could be done:
        ensuring the file exists
        ensuring the parent path exists
        ensuring there are no control characters in the filename
        ..etc.
    """
    name = 'file path'

    def __init__(self, value):
        if not isinstance(value, (str, unicode)):
            msg = '"{}" is not a recognized filepath.'
            raise ValueError(msg.format(value))


class TimeString24(DataType):
    name = '24hr time string'

    def __init__(self, value):
        try:
            datetime.strptime(value, "%H:%M:%S")
        except (ValueError, TypeError):
            msg = '"{}" is not a recognized HH:MM:SS time.'
            raise ValueError(msg.format(value))


class ConsoleKeymap(DataType):
    _locales = {os.path.basename(p) for p in glob('/usr/share/locale/*')[0]}
    name = 'console keymap'

    def __init__(self, value):
        if value not in self._locales:
            raise ValueError("Unknown locale: {}".format(value))


class Password(DataType):
    name = 'password'

    def __init__(self, value):
        if not isinstance(value, str):
            msg = '"{}" is not a string (passwords must be strings)'
            raise TypeError(msg.format(value))


class HorizSyncRate(DataType):
    name = 'horizontal sync rate'

    def __init__(self, value):
        print "HorizSyncRate:"
        print "   Max/min rates (or whether or not ddcprobe will be installed,"
        print "   for example) are not known.  What should the angle of"
        print "   attack be here? --value checked only that it is a number."
        Integer(value)


class VertRefreshRate(DataType):
    name = 'vertical refresh rate'

    def __init__(self, value):
        print "VertRefreshRate:"
        print "   Max/min rates (or whether or not ddcprobe will be installed,"
        print "   for example) are not known.  What should the angle of"
        print "   attack be here? --value checked only that it is a number."
        Integer(value)


class ColorDepth(DataType):
    _allowed_values = ['8', '16', '24', '32']
    name = 'color depth'

    def __init__(self, value):
        if value not in self._allowed_values:
            msg = "Invalid value: {}.  Color depth must be one of: {}"
            raise ValueError(msg.format(value, repr(self._allowed_values)))


def get_data_types():
    globl = globals()
    return {globl[obj].name for obj in globl
            if type(globl[obj]) == type
            and issubclass(globl[obj], DataType)
            and globl[obj] is not DataType}


def get_data_type_dict():
    globl = globals()
    pairs = [(globl[obj].name, globl[obj]) for obj in globl
             if type(globl[obj]) == type
             and issubclass(globl[obj], DataType)
             and globl[obj] is not DataType]
    return dict(pairs)


class Validator(object):
    """Instantiate a validator, then use the 'validate' method to check data
    against the expected data type.  These are not python data types, but
    rather types defined within this module."""
    def __init__(self):
        self.data_types = get_data_type_dict()

    def add_data_type(self, data_type):
        self.data_types[data_type.name] = data_type

    def validate(self, expected_data_type, value):
        """validate(typename, value) -> None if valid, Error message otherwise.
        Validate that a value fits its expected type.
        expected_data_type is a registered data type name, like "ip address".
        A full set of data types can be acquired by doing:
            import data_validation
            data_validation.get_data_types()
        """
        try:
            self.data_types[expected_data_type](value)
        except ValueError, e:
            return e.message

class LTSPValidator(Validator):
    def __init__(self, lts_vars_config_obj):
        super(LTSPValidator, self).__init__()
        self.vars_meta = lts_vars_config_obj

    def check_data(self, option, value):
        """Check an option/value pair to see if it is proper according to the
        data in the LTSVarsConfig object that is passed in at runtime.
        """
        if option not in self.vars_meta:
            msg = "Warning: Read unknown option '%s' from LTS config."
            print msg % option
        else:
            var_meta = self.vars_meta[option]
            error = self.validate(var_meta.datatype, value)
            if error:
                msg = "Warning: Bad content (%s) in LTS config for %s: %s"
                return msg % (value, option, error)