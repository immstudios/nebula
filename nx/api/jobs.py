#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_jobs"]

def api_jobs(**kwargs):
    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())

    return {"response" : 501, "message" : "Not implemented"}
