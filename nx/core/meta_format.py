import time

from nxtools import *
from .constants import *

if PYTHON_VERSION < 3:
    str_type = unicode
else:
    str_type = str

#
#
#

def format_numeric(meta_type, value, **kwargs):
    return "{:.03d}".format(value)

def format_boolean(meta_type, value, **kwargs):
    #TODO: web version, qt version etc
    return ["no", "yes"][bool(value)]

def format_datetime(meta_type, value, **kwargs):
    time_format = kwargs.get("time_format", "%Y-%m-%d %H:%M")
    return time.strftime(time_format, time.localtime(value))

def format_timecode(meta_type, value, **kwargs):
    return s2time(value)

def format_regions(meta_type, value, **kwargs):
    return "{} regions".format(len(value))

def format_fract(meta_type, value, **kwargs):
    return value # TODO

def format_select(meta_type, value, **kwargs):
    return value # TODO

def format_list(meta_type, value, **kwargs):
    return value # TODO


humanizers = {
        -1       : None,
        STRING   : None,
        TEXT     : None,
        INTEGER  : None,
        NUMERIC  : format_numeric,
        BOOLEAN  : format_boolean,
        DATETIME : format_datetime,
        TIMECODE : format_timecode,
        REGIONS  : format_regions,
        FRACTION : format_fract,
        SELECT   : format_select,
        LIST     : format_list
    }
