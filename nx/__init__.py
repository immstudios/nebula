from nebulacore import *

from .connection import *
from .objects import *
from .helpers import *
from .api import *
from .base_service import *


def load_settings(force=False):
    global config
    # This is the first time we are connecting DB
    # so error handling should be here
    try:
        db = DB()
    except Exception:
        message = log_traceback("Database connection error", handlers=False)
        critical_error("Unable to connect nebula database")

    # Load from db

    db.query("SELECT key, value FROM settings")
    for key, value in db.fetchall():
        config[key] = value

    db.query("SELECT id, settings FROM storages")

    for id, settings in db.fetchall():
        config["storages"][id] = settings

    db.query("SELECT id, channel_type, settings FROM channels")
    for id, channel_type, settings in db.fetchall():
        if channel_type == 0:
            config["playout_channels"][id] = settings
#TODO: Ingest channels
#        elif channel_type == 1:
#            config["ingest_channels"][id] = settings

    db.query("SELECT id, settings FROM folders")
    for id, settings in db.fetchall():
        config["folders"][id] = settings

    db.query("SELECT key, settings FROM meta_types")
    for key, settings in db.fetchall():
        config["meta_types"][key] = settings

    db.query("SELECT cs, value, settings FROM cs")
    for cst, value, settings in db.fetchall():
        if not cst in config["cs"]:
            config["cs"][cst] = []
        config["cs"][cst].append([value, settings])

    db.query("SELECT id, title, settings, owner, position FROM views")
    for id, title, settings, owner, position in db.fetchall():
        settings = xml(settings)
        view = {"title" : title, "columns" : [], "position" : position}
        columns = settings.find("columns")
        if columns is not None:
            for column in columns.findall("column"):
                if column.text:
                    view["columns"].append(column.text.strip())
        for elm in ["folders", "media_types", "content_types", "statuses"]:
            try:
                d = settings.find(elm)
                if d is not None:
                    view[elm] = [int(x.strip()) for x in d.text.split(",")]
            except Exception:
                log_traceback()
        config["views"][id] = view

    db.query("SELECT id, service_type, title FROM actions")
    for id, service_type, title in db.fetchall():
        config["actions"][id] = {
                    "title" : title,
                    "service_type" : service_type,
                    "title" : title
                }

    #
    # Init all
    #

    messaging.configure()
    cache.configure()
    return True

load_settings()

from .plugins import *
