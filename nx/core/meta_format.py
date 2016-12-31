import time

from nxtools import *

from .common import *
from .constants import *

if PYTHON_VERSION < 3:
    str_type = unicode
else:
    str_type = str

#
# Formating helpers
#

def format_integer(meta_type, value, **kwargs):
    value = int(value)
    if kwargs.get("mode", False) == "hub":
        if not value and meta_type.settings.get("hide_null", False):
            return ""
        if meta_type.key == "id_folder":
            fconfig = config["folders"][value]
            return "<span class=\"label\" style=\"background-color : #{:06x}\">{}</span>".format(fconfig["color"], fconfig["title"])
    return value


def format_numeric(meta_type, value, **kwargs):
    return "{:.03f}".format(value)


def format_boolean(meta_type, value, **kwargs):
    value = int(value)
    if kwargs.get("mode", False) == "hub":
        if meta_type.key == "promoted":
            return [
                    "<i class=\"mdi mdi-star-outline\">",
                    "<i class=\"mdi mdi-star\">"
                ][value]
        else:
            return [
                    "<i class=\"mdi mdi-checkbox-blank-outline\">",
                    "<i class=\"mdi mdi-checkbox-marked-outline\">"
                ][value]
    return ["no", "yes"][bool(value)]


def format_datetime(meta_type, value, **kwargs):
    time_format = meta_type.settings.get("format", False) or kwargs.get("format", "%Y-%m-%d %H:%M")
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
        INTEGER  : format_integer,
        NUMERIC  : format_numeric,
        BOOLEAN  : format_boolean,
        DATETIME : format_datetime,
        TIMECODE : format_timecode,
        REGIONS  : format_regions,
        FRACTION : format_fract,
        SELECT   : format_select,
        LIST     : format_list
    }
