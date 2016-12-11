from .core import *
from .connection import *
from .objects import *
from .helpers import *
from .api import *


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
    config["views"] = {}
    config["asset_types"] = {}
    config["meta_types"] = {}
    config["cs"] = {}

    # Load from db

    db.query("SELECT key, value FROM settings")
    for key, value in db.fetchall():
        config[key] = value

    db.query("SELECT id, title, settings FROM storages")
    for id, title, settings in db.fetchall():
        config["storages"][id] = settings
        config["storages"][id]["title"] = title

    db.query("SELECT id, title, channel_type, settings FROM channels")
    for id, title, channel_type, settings in db.fetchall():
        pass #TODO

    db.query("SELECT id, title, settings, owner, position FROM views")
    for id, title, settings, owner, position in db.fetchall():
        pass #TODO

    db.query("SELECT id, title, settings FROM asset_types")
    for id, title, settings in db.fetchall():
        config["meta_types"][key] = settings

    db.query("SELECT key, settings FROM meta_types")
    for key, settings in db.fetchall():
        config["meta_types"][key] = settings

    db.query("SELECT cs, key, value, settings FROM cs")
    for cs, key, value, settings in db.fetchall():
        pass #TODO

    #
    # Init all
    #

    messaging.configure()
    cache.configure()
    return True



load_settings()
