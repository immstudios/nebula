import time

from nxtools import *

from .common import *
from .constants import *

__all__ = ["meta_types", "MetaType", "cs"]


if PYTHON_VERSION < 3:
    str_type = unicode
else:
    str_type = str

#
# Classification sheets
#

class ClassificationSheet():
    def __init__(self):
        pass
#TODO: Big TODO


class CS():
    def __init__(self):
        self.sheets = {}

    def __getitem__(self, key
        return self.sheets[key

#
# Validators
#

class NebulaInvalidValueError(Exception):
    pass


def validate_string(meta_type, value):
    return to_unicode(value)

def validate_text(meta_type, value):
    return to_unicode(value)

def validate_integer(meta_type, value):
    try:
        value = int(value)
    except ValueError:
        raise NebulaInvalidValueError #TODO: be more or less specific
    return value

def validate_numeric(meta_type, value):
    #TODO
    return value

def validate_boolean(meta_type, value):
    #TODO
    return value

def validate_datetime(meta_type, value):
    #TODO
    return value

def validate_timecode(meta_type, value):
    #TODO
    return value

def validate_regions(meta_type, value):
    #TODO
    return value

def validate_fract(meta_type, value):
    string = value.replace(":", "/")
    split = string.split("/")
    assert len(split) == 2 and split[0].is_digit() and split[1].is_digit()
    return string

def validate_select(meta_type, value):
    #TODO
    return value

def validate_list(meta_type, value):
    #TODO
    return value



#
# Humanizers
# functions returning a human readable representation of the meta value
# since it may be used anywhere (admin, front end) additional rendering params can be passed
#

def humanize_numeric(meta_type, value, **kwargs):
    return "{:.03d}".format(value)

def humanize_boolean(meta_type, value, **kwargs):
    #TODO: web version, qt version etc
    return ["no", "yes"][bool(value)]

def humanize_datetime(meta_type, value, **kwargs):
    time_format = kwargs.get("time_format", "%Y-%m-%d %H:%M")
    return time.strfitme(time_format, time.localtime(value))

def humanize_timecode(meta_type, value, **kwargs):
    return s2time(value)

def humanize_regions(meta_type, value, **kwargs):
    return "{} regions".format(len(value))

def humanize_select(meta_type, value, **kwargs):
    return value # TODO

def humanize_list(meta_type, value, **kwargs):
    return value # TODO

#
# Puting it all together
#

class MetaType():
    def __init__(self, key, **kwargs):
        self.key = key
        self.settings = {
                "fulltext" : False,
                "editable" : False,
                "class" : STRING
            }
        self.settings.update(kwargs)
        self.humanizer = {
                STRING : None,
                TEXT : None,
                INTEGER : None,
                NUMERIC : humanize_numeric,
                BOOLEAN : humanize_boolean,
                DATETIME : humanize_datetime,
                TIMECODE : humanize_timecode,
                REGIONS : humanize_regions,
                FRACTION : None,
                SELECT : humanize_select,
                LIST : humanize_list,
            }[self["class"]]

        self.validator = {
                STRING : validate_string,
                TEXT : validate_text,
                INTEGER : validate_integer,
                NUMERIC : validate_numeric,
                BOOLEAN : validate_boolean,
                DATETIME : validate_datetime,
                TIMECODE : validate_timecode,
                REGIONS : validate_regions,
                FRACTION : validate_fraction,
                SELECT : validate_select,
                LIST : validate_list,
            }[self["class"]]

    def __getitem__(self, key):
        return self.settings[key]

    @property
    def default(self):
        # TODO
        return None

    @property
    def default_alias(self):
        return self.key.replace("_"," ").capitalize()

    def alias(self, lang="en"):
        #TODO
        return self.default_alias

    def header(self, lang="en"):
        #TODO
        return self.default_alias

    def validate(self, value):
        if self.validator:
            return self.validator(self, value)
        return value

    def humanize(self, value, **kwargs):
        if not self.humanizer:
            return self.humanizer(self, value, **kwargs)



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
        return {key : self[key].settings for key in self.data.keys()}

    def load_from_dump(self, dump):
        self.data = {}
        for key in dump:
            self.data[key] = MetaType(key, dump[key])

#
#
#

meta_types = MetaTypes()
cs = CS()
