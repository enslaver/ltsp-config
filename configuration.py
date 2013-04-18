# -*- coding: utf-8 -*-
"""This is a module for storing classes and methods relating to parsing
configuration data from config files and representing it in a useful way."""

from collections import namedtuple
import ConfigParser
import data_validation

## To add new permitted data types to the LTSVarsConfig (and consequently to
#  the configuration files) make a new DataType subclass in the data_validation
#  module.  This is very straightforward, there are many examples, and it is
#  explained at the bottom of the module docstring.
VALID_DATATYPES = data_validation.get_data_types()


# the model for the configuration of a single variable
VarConfig = namedtuple('LTSVarOptions', 'name datatype default description')


class LTSVarsConfig(object):
    """A container object which parses and represents configuration data for
    the variable options (typically in lts.conf.options) for the ltsp-config
    project.
    Each entry in the configuration file is represented in this container as
    an LTSVarOptions instance (a namedtuple), with a name, data type, default
    value, and description (members: name, datatype, default, description).
    This class works both like a dict and like a list.  Like a dict, variable
    names looked up with __getitem__ (as in conf['VAR_NAME']) will return their
    respective data.  However, iterating works like a list -- iterating over
    the instance will yield values, not names.  Lastly, doing lookups with a
    numerical reference will index into the config like a list as well.  It is
    acceptable to have both strings and indexes referenced via the __getitem__
    method since variable names from the file will *always* be strings.
    Examples:
        >>> conf = LTSVarsConfig('valid_vars_config_file')
        >>> conf[0]    # list-style indexing
        LTSVarOptions(name='CONFIGURE_FSTAB', datatype='boolean',
                      default='True', description='/etc/fstab is blah blah..')
        >>> conf['CONFIGURE_FSTAB']
        LTSVarOptions(name='CONFIGURE_FSTAB', datatype='boolean',
                      default='True', description='/etc/fstab is blah blah..')
        for var in conf:
            print var.name, var.datatype, var.default, var.description
        <prints name, datatype, var.default, var.description>
    ### Config file syntax ###
    Config file syntax is as follows:
        # comments start with a hash.  Whitespace around colon is ignored.
        <LTSP_VARIABLE> : <fieldtype>, default <value> : <description>
        <LTSP_VAR01...LTSP_VAR45>:<fieldtype>, default <value>:<description>
    Example:
        CONFIGURE_FSTAB:boolean, default True: blah blah foo bar baz
        # lots of these ones..
        CRONTAB_01...CRONTAB_10: string, default unset : description here
    ..the above example config would generate 11 entries -- one each for
    CRONTAB_01 through CRONTAB_10, and one for CONFIGURE_FSTAB.
    """
    def __init__(self, lts_conf_fname):
        self.fname = lts_conf_fname
        raw_data = open(self.fname).readlines()
        self._data_list = []
        self._data_dict = {}
        lineno = 0
        for line in raw_data:
            lineno += 1
            # handle comment lines
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            values = line.split(':', 2)
            if not len(values) == 3:
                print "Invalid line (%d) in config: %s" % (lineno, line)
                continue
            name, typedefault, description = values
            values = typedefault.strip().split(', default ')
            if not len(values) == 2:
                print "Invalid line (%d) in config: %s" % (lineno, line)
                continue
            datatype, default = [v.strip() for v in values]
            datatype = datatype.lower()
            if datatype not in VALID_DATATYPES:
                msg = "Unknown datatype '%s' on line %d in %s"
                print msg % (datatype, lineno, self.fname)
                continue

            description = description.replace(r'\n', '\n').strip()
            if '...' in name:
                self._handle_ranged_names(lineno, name, datatype, default,
                                          description)
            else:
                item = VarConfig(name, datatype, default, description)
                self._data_list.append(item)
                self._data_dict[item.name] = item

    def __contains__(self, name):
        """'foo' in conf -> True if conf contains info for a variable foo
        """
        return name in self._data_dict

    def __getitem__(self, ref):
        """Allows items to be fetched either by their index or by their name.
        """
        if isinstance(ref, int):
            return self._data_list[ref]
        else:
            return self._data_dict[ref]

    def __iter__(self):
        return (entry for entry in self._data_list)

    def _handle_ranged_names(self, lineno, name, datatype, default,
                             description):
        """Some names contain ellipses, as in:
            X_FOO_01...X_FOO_10
            ..this method creates a range of names to fulfill this, and makes
            an entry for each.  For this to work, the names must be identical
            until the numerical part, and separated by ellipses (...).
        """
        left, right = name.split('...')
        if len(left) != len(right):
            reason = "invalid names for range value: %s and %s"
            message = "Invalid line (%d) in config -- " + reason
            print message % (lineno, left, right)
            return
        for needle in xrange(0, len(left)):
            if left[needle] != right[needle]:
                break
        try:
            num_len = len(left[needle:])
            # this will end with a string like:
            # FOO_BASENAME_%02d
            # ..which will be used to assemble names.
            base_name = left[:needle] + '%0' + str(num_len) + 'd'
            left_value = int(left[needle:])
            right_value = int(right[needle:])
        except ValueError:
            reason = "invalid number in names for range value: %s and %s"
            message = "Invalid line (%d) in config -- " + reason
            print message % (lineno, left, right)
        names = [base_name % i for i in xrange(left_value, right_value)]
        for numbered_name in names:
            item = VarConfig(numbered_name, datatype, default, description)
            self._data_list.append(item)
            self._data_dict[item.name] = item

    def __repr__(self):
        return 'LTSVarsConfig(%s)' % self.fname

    @property
    def vars(self):
        return [v.name for v in self._data_list]


class __Parser(object):
    name = None
    def a(self, name = None):
        if name:
            self.name = name
            self.add_section(self.name)
    def s(self, key = None, value = None, name = None):
        if name:
            self.name = name
        if self.name and key:
            self.set(self.name, key, value)
    def w(self, file):
        with open(file, 'wb') as c:
            self.write(c)


class Conf(ConfigParser.ConfigParser, __Parser):
    pass


class Raw(ConfigParser.RawConfigParser, __Parser):
    pass


class Safe(ConfigParser.SafeConfigParser, __Parser):
    pass
