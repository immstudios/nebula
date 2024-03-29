__all__ = ["api_send"]

from nxtools import logging

from nx.core.common import NebulaResponse
from nx.db import DB
from nx.jobs import send_to
from nx.objects import anonymous


def api_send(**kwargs):
    objects = kwargs.get("objects") or kwargs.get(
        "ids", []
    )  # TODO: ids is deprecated. use objects instead
    id_action = kwargs.get("id_action", False)
    settings = kwargs.get("settings", {})
    db = kwargs.get("db", DB())
    user = kwargs.get("user", anonymous)
    restart_existing = kwargs.get("restart_existing", True)
    restart_running = kwargs.get("restart_running", False)

    if not user.has_right("job_control", anyval=True):
        return NebulaResponse(403, "You are not allowed to execute this action")
        # TODO: Better ACL

    if not id_action:
        return NebulaResponse(400, "No valid action selected")

    if not objects:
        return NebulaResponse(400, "No asset selected")

    if not user.has_right("job_control", id_action):
        return NebulaResponse(400, "You are not allowed to start this action")

    logging.info(
        "{} is starting action {} for the following assets: {}".format(
            user, id_action, ", ".join([str(i) for i in objects])
        )
    )

    for id_object in objects:
        send_to(
            id_object,
            id_action,
            settings=settings,
            id_user=user.id,
            restart_existing=restart_existing,
            restart_running=restart_running,
            db=db,
        )

    return NebulaResponse(
        200, "Starting {} job{}".format(len(objects), "s" if len(objects) > 1 else "")
    )
