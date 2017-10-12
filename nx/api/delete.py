#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_delete"]

def api_delete(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}

    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    return {"response" : 501, "message" : "Not implemented"}

