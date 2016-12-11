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

def validate_default(meta_type, value):
    if type(value) in [str, str_type, float, int, list, dict]:
        return value
    return str(value)

def validate_string(meta_type, value):
    if type(value) in (int, float):
        return str(value)
    return to_unicode(value).strip()

def validate_text(meta_type, value):
    if type(value) in (int, float):
        return str(value)
    return to_unicode(value).strip()

def validate_integer(meta_type, value):
    try:
        value = int(value)
    except ValueError:
        raise NebulaInvalidValueError
    return value

def validate_numeric(meta_type, value):
    if type(value) in [int, float]:
        return value
    try:
        return float(value)
    except ValueError:
        raise NebulaInvalidValueError

def validate_boolean(meta_type, value):
    if value:
        return True
    return False

def validate_datetime(meta_type, value):
    return validate_numeric(meta_type, value)

def validate_timecode(meta_type, value):
    return validate_numeric(meta_type, value)

def validate_regions(meta_type, value):
    return value

def validate_fract(meta_type, value):
    value = value.replace(":", "/")
    split = value.split("/")
    assert len(split) == 2 and split[0].isdigit() and split[1].isdigit()
    return value

def validate_select(meta_type, value):
    #TODO
    return value

def validate_list(meta_type, value):
    #TODO
    return value



validators = {
        -1       : validate_default,
        STRING   : validate_string,
        TEXT     : validate_text,
        INTEGER  : validate_integer,
        NUMERIC  : validate_numeric,
        BOOLEAN  : validate_boolean,
        DATETIME : validate_datetime,
        TIMECODE : validate_timecode,
        REGIONS  : validate_regions,
        FRACTION : validate_fract,
        SELECT   : validate_select,
        LIST     : validate_list
    }
