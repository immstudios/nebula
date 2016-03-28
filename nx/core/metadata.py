import time

from nxtools import *

from .common import *
from .constants import *


__all__ = ["meta_types", "MetaType"]


if PYTHON_VERSION < 3:
    str_type = unicode
else:
    str_type = str


def validate_fract(string):
    string = string.replace(":", "/")
    split = string.split("/")
    assert len(split) == 2 and split[0].is_digit() and split[1].is_digit()
    return string


format_ops = {
#       CLASS       TYPE        VALIDATOR          DEFAULT   HUMANIZER
        -1        : [object,    lambda x: x,       None,     None],
        TEXT      : [str_type,  to_unicode,        "",       None],
        BLOB      : [str_type,  to_unicode,        "",       None],
        INTEGER   : [int,       None,              0,        None],
        NUMERIC   : [float,     None,              0,        lambda key, x: "{:03d}".format(x)],
        BOOLEAN   : [bool,      None,              False,    lambda key, x: str(bool(x))],
        DATETIME  : [float,     None,              0,        lambda key, x: time.strfitme("%Y-%m-%d %H:%M", time.localtime(x))],
        TIMECODE  : [float,     None,              0,        lambda key, x: s2time(x)],
        REGIONS   : [list,      None,              [],       lambda key, x: "{} regions".format(len(x))],
        FRACTION  : [str_type,  validate_fract,    "1/1",    None],
        SELECT    : [str_type,  None,              "",       None],
        CS_SELECT : [str_type,  None,              "",       None],
        ENUM      : [int,       None,              0,        None],
        CS_ENUM   : [int,       None,              0,        None],
        LIST      : [list,      None,              [],       lambda key, x: ", ".join(x)],
    }


class MetaType():
    def __init__(self, key):
        self.key        = key
        self.namespace  = "site"
        self.editable   = False
        self.searchable = False
        self.meta_class = -1
        self.settings   = False
        self.aliases    = {}

    @property
    def default(self):
        return format_ops[self.meta_class][2]

    @property
    def dump(self):
        return {
                "key"        : self.key,
                "namespace"  : self.namespace,
                "editable"   : self.editable,
                "searchable" : self.searchable,
                "class"      : self.meta_class,
                "settings"   : self.settings,
                "aliases"    : self.aliases
            }

    @property
    def default_alias(self):
            return self.key.replace("_"," ").capitalize()

    def alias(self, lang="en-US"):
        if not lang in self.aliases:
            return self.default_alias
        return self.aliases[lang][0]

    def col_header(self, lang="en-US"):
        if not lang in self.aliases:
            return self.default_alias
        a, h = self.aliases[lang]
        if h is None:
            return a
        return h



class MetaTypes():
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data.get(key, MetaType(key))

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return self.data.__iter__()

    @property
    def dump(self):
        return [meta_type.dump for meta_type in self]

    def ensure_format(self, key, value):
        target_class = self[key].meta_class
        target_type, validator, default, humanizer = format_ops[target_class]
        if validator:
            return validator(value)
        elif target_type == type(value):
            return value
        else:
            return target_type(value)

    def humanize(self, key, value, **kwargs):
        target_class = self[key].meta_class
        humanizer = format_ops[target_class][3]
        if not humanizer:
            return value
        return humanizer(key, value)



meta_types = MetaTypes()
