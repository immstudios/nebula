#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_send"]

def api_send(**kwargs):
    return {"response" : 501, "message" : "Not implemented"}

    ids       = kwargs.get("ids", [])
    id_action = kwargs.get("id_action", False)
    settings  = kwargs.get("settings", {})
    restart   = params.get("restart", True)
    user      = kwargs.get("user", anonymous)
    db        = kwargs.get("db", DB())

    if not id_action:
        return {"response" : 400, "message" : "No valid action selected"}

    if not ids:
        return {"response" : 400, "message" : "No asset selected"}

    if not user.has_right("job_control", id_action):
        return {"response" : 403, "message" : "You are not allowed to start this action"}

    logging.info("{} is starting action {} for following assets: {}".format(user, id_action, ", ".join(ids) ))

    db = DB()
    for id_object in ids:
        send_to(id_object, id_action, settings=settings, id_user=user.id, restart=restart, db=db)

    return {"response" : 202, "message" : "Starting {} jobs".format(len(ids))}

