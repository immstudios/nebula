__all__ = ["api_system"]

import time

from nxtools import logging

from nx import DB, config, NebulaResponse
from nx.objects import anonymous


def api_system(**kwargs):
    """
    Returns system status and controls services
    Arguments:

    request       list of information to show.
                  defaults to everything ["services", "hosts"]
    stop          stop service by its ID
    start         start service by its ID
    kill          kill service by its ID
    set_autostart toggle service autostart param (True/False)
    """

    user = kwargs.get("user", anonymous)
    message = ""
    if not user:
        return NebulaResponse(401)

    db = DB()

    request = kwargs.get("request", ["services", "hosts"])

    if "stop" in kwargs:
        id_service = kwargs["stop"]
        if not type(id_service) == int:
            return NebulaResponse(400, "Invalid ID service to stop")
        if not user.has_right("service_control", id_service):
            return NebulaResponse(403, "You are not allowed to control this service")
        db.query("UPDATE services SET state=3 WHERE id=%s AND state = 1", [id_service])
        db.commit()
        logging.info(
            f"{user} requested service ID {id_service} ({config['services'][id_service]['title']}) stop"
        )
        message = "Service is stopping"

    if "start" in kwargs:
        id_service = kwargs["start"]
        if not type(id_service) == int:
            return NebulaResponse(400, "Invalid ID service to start")
        if not user.has_right("service_control", id_service):
            return NebulaResponse(403, "You are not allowed to control this service")
        db.query("UPDATE services SET state=2 WHERE id=%s AND state = 0", [id_service])
        db.commit()
        logging.info(
            f"{user} requested service ID {id_service} ({config['services'][id_service]['title']}) start"
        )
        message = "Service is starting"

    if "kill" in kwargs:
        id_service = kwargs["kill"]
        if not type(id_service) == int:
            return NebulaResponse(400, "Invalid ID service to kill")
        if not user.has_right("service_control", id_service):
            return NebulaResponse(403, "You are not allowed to control this service")
        db.query("UPDATE services SET state=4 WHERE id=%s AND state = 3", [id_service])
        db.commit()
        logging.info(
            f"{user} requested service ID {id_service} ({config['services'][id_service]['title']}) kill"
        )
        message = "Attempting to kill the service"

    if "autostart" in kwargs:
        id_service = kwargs["autostart"]
        if not type(id_service) == int:
            return NebulaResponse(400, "Invalid ID service to set autostart")
        if not user.has_right("service_control", id_service):
            return NebulaResponse(403, "You are not allowed to control this service")
        db.query(
            "UPDATE services SET autostart=NOT autostart WHERE id=%s", [id_service]
        )
        logging.info(
            f"{user} requested service ID {id_service} ({config['services'][id_service]['title']}) autostart"
        )
        db.commit()
        message = "Service auto-start updated"

    result = {}
    if "services" in request:
        services = []
        db.query(
            "SELECT id, service_type, host, title, autostart, state, last_seen FROM services ORDER BY id ASC"
        )
        for id, service_type, host, title, autostart, state, last_seen in db.fetchall():
            service = {
                "id": id,
                "type": service_type,
                "host": host,
                "title": title,
                "autostart": autostart,
                "state": state,
                "last_seen": last_seen,
                "last_seen_before": time.time() - last_seen,
            }
            services.append(service)
        result["services"] = services

    if "hosts" in request:
        hosts = []
        db.query("SELECT hostname, last_seen, status FROM hosts ORDER BY hostname")
        for hostname, last_seen, status in db.fetchall():
            host = status
            host["hostname"] = hostname
            host["last_seen"] = last_seen
            hosts.append(host)
        result["hosts"] = hosts

    return NebulaResponse(200, data=result, message=message)
