from .common import *
from .constants import *
from .meta_validate import validators
from .meta_format import humanizers

__all__ = ["meta_types", "MetaType"]


default_meta_type = {
        "ns"       : "m",
        "class"    : -1,
        "fulltext" : 0,
        "editable" : 0,
        "aliases"  : {}
    }


defaults = {
        -1       : None,
        STRING   : "",
        TEXT     : "",
        INTEGER  : 0,
        NUMERIC  : 0,
        BOOLEAN  : False,
        DATETIME : 0,
        TIMECODE : 0,
        REGIONS  : [],
        FRACTION : "1/1",
        SELECT   : "",
        LIST     : []
    }


class MetaType(object):
    def __init__(self, key, settings):
        self.key = key
        self.settings = settings or default_meta_type
        self.validator = validators[self["class"]]
        self.humanizer = humanizers[self["class"]]

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value

    @property
    def default(self):
        if "default" in self.settings:
            return self["default"]
        return defaults[self["class"]]

    @property
    def default_alias(self):
        return self.key.split("/")[-1].replace("_"," ").capitalize()

    def alias(self, lang="en"):
        if lang in self.settings["aliases"]:
            return self.settings["aliases"][lang][0]
        return self.default_alias

    def header(self, lang="en"):
        if lang in self.settings["aliases"]:
            return self.settings["aliases"][lang][1]
        return self.default_alias

    def validate(self, value):
        if self.validator:
            return self.validator(self, value)
        return value

    def show(self, value, **kwargs):
        if not self.humanizer:
            return value
        return self.humanizer(self, value, **kwargs)


class MetaTypes(object):
    def __getitem__(self, key):
        return MetaType(key, config["meta_types"].get(key, None))

    def __setitem__(self, key, value):
        if type(value) == MetaType:
            data = value.settings
        elif type(value) == dict:
            data = value
        else:
            return
        config["meta_types"][key] = data

    def __iter__(self):
        return config["meta_types"].__iter__()


meta_types = MetaTypes()
