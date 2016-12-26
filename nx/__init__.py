from .core import *
from .connection import *
from .objects import *
from .helpers import *
from .api import *
from .base_service import *
from .plugins import *


def load_settings(force=False):
    global config

    logging.debug("Loading site configuration from DB", handlers=False)

    # This is the first time we are connecting DB
    # so error handling should be here
    try:
        db = DB()
    except Exception:
        log_traceback(handlers=False)


    config["storages"] = {}
    config["playout_channels"] = {}
    config["ingest_channels"] = {}
    config["folders"] = {}
    config["meta_types"] = {}
    config["cs"] = {}
    config["views"] = {}

    # Load from db

    db.query("SELECT key, value FROM settings")
    for key, value in db.fetchall():
        config[key] = value

    db.query("SELECT id, settings FROM storages")
    for id, title, settings in db.fetchall():
        config["storages"][id] = settings

    db.query("SELECT id, channel_type, settings FROM channels")
    for id, channel_type, settings in db.fetchall():
        pass #TODO

    db.query("SELECT id, settings FROM folders")
    for id, settings in db.fetchall():
        config["folders"][id] = settings

    db.query("SELECT key, settings FROM meta_types")
    for key, settings in db.fetchall():
        config["meta_types"][key] = settings

    db.query("SELECT cs, key, value, settings FROM cs")
    for cs, key, value, settings in db.fetchall():
        pass #TODO

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

    #
    # Init all
    #

    messaging.configure()
    cache.configure()
    return True



load_settings()
