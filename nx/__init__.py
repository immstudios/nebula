from .core import *
from .connection import *
from .objects import *
from .helpers import *

#
# Load system configuration
#

def load_site_settings(db):
    global config
    site_settings = {
               "playout_channels" : {},
               "ingest_channels" : {},
               "views" : {},
               "asset_types" : {}
            }

    # Settings

    db.query("SELECT key, value FROM settings")
    for key, value in db.fetchall():
        site_settings[key] = value

    # Views

    db.query("SELECT id, settings FROM views")
    for id, settings in db.fetchall():
        settings = xml(settings)
        view = {}
        for elm in ["query", "asset_type", "origin", "media_type", "content_type", "status"]:
            try:
                view[elm] = settings.find(elm).text.strip()
            except:
                continue
        site_settings["views"][id] = view

    # Channels

    db.query("SELECT id, title, channel_type, settings FROM channels")
    for id, title, channel_type, settings in db.fetchall():
        settings["title"] = title
        if channel_type == PLAYOUT:
            site_settings["playout_channels"][id] = settings
        elif channel_type == INGEST:
            site_settings["ingest_channels"][id] = settings
    config.update(site_settings)
    return True



def load_storages(db, force=False):
    global storages
    db.query("SELECT id, title, settings FROM storages")
    for id, title, settings in db.fetchall():
        storage = Storage(id, title, **settings)
        storages.add(storage)
    return True

#
# Load metadata model
#

def load_meta_types(db, force=False):
    global meta_types
#TODO: load from cache
    db.query("SELECT key, settings FROM meta_types")
    for key, settings in db.fetchall():
        meta_type = MetaType(key, **settings)
        meta_types[key] = meta_type
#TODO: load aliases
#TODO: save to cache
    return True


def load_cs(db, force=False):
    pass

#
# Do it! Do it! Do it!
#

def load_all_settings(force=False):
    logging.debug("Loading site configuration from DB", handlers=False)
    try:
        # This is the first time we are connecting DB so error handling should be here
        db = DB() 
    except:
        log_traceback(handlers=False)
        critical_error("Unable to connect database", handlers=False)
    load_site_settings(db, force)
    load_storages(db, force)
    load_meta_types(db, force)
    load_cs(db, force)
    messaging.configure()

load_all_settings()
