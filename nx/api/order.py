#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_order"]

def api_order(**kwargs):
    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    return {"response" : 501, "message" : "Not implemented"}

