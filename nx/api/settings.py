#
# Returns system settins
#

from nx import *

__all__ = ["api_settings"]

def api_settings(**kwargs):
    return {'response' : 200, 'data' : config}
