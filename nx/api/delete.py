#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_delete"]

def api_delete(**kwargs):
    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    return {"response" : 501, "message" : "Not implemented"}

