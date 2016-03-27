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
        -1        : [object,    lambda x: x],
        TEXT      : [str_type,  to_unicode],
        BLOB      : [str_type,  to_unicode],
        INTEGER   : [int,       None],
        NUMERIC   : [float,     None],
        BOOLEAN   : [bool,      None],
        DATETIME  : [float,     None],
        TIMECODE  : [float,     None],
        REGIONS   : [list,      None],
        FRACTION  : [str_type,  validate_fract],
        SELECT    : [str_type,  None],
        CS_SELECT : [str_type,  None],
        ENUM      : [int,       None],
        CS_ENUM   : [int,       None],
        LIST      : [list,      None],
    }


class MetaType():
    def __init__(self, key):
        self.key        = key
        self.namespace  = "site"
        self.editable   = False
        self.searchable = False
        self.meta_class = -1
        self.default    = False
        self.settings   = False
        self.aliases    = {}

    @property
    def dump(self):
        return {
                "key"        : self.key,
                "namespace"  : self.namespace,
                "editable"   : self.editable,
                "searchable" : self.searchable,
                "class"      : self.meta_class,
                "default"    : self.default,
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
        self.data.get(key, MetaType())

    def __iter__(self):
        return self.data.__iter__()

    @property
    def dump(self):
        return [meta_type.dump for meta_type in self]

    def ensure_format(self, key, value):
        target_class = self[key].target_class
        target_type, validator = format_ops[target_class]
        if validator:
            return validator(value)
        elif target_type == type(value):
            return value
        else:
            return target_type(value)



meta_types = MetaTypes()
