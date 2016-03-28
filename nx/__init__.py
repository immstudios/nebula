from .core import *
from .db import *
from .objects import *
from .helpers import *


def load_site_settings(db):
    global config
    config["playout_channels"] = {}
    config["ingest_channels"] = {}
    config["views"] = {}

    #
    # Site settings
    #

    db.query("SELECT key, value FROM settings")
    for key, value in db.fetchall():
        config[key] = value

    #
    # Views
    #

    db.query("SELECT id, settings FROM views")
    for id, settings in db.fetchall():
        settings = xml(settings)
        view = {}
        for elm in ["query", "folders", "origins", "media_types", "content_types", "statuses"]:
            try:
                view[elm] = settings.find(elm).text.strip()
            except:
                continue
        config["views"][id] = view

    #
    # Channels
    #

    db.query("SELECT id, channel_type, title, settings FROM channels")
    for id_channel, channel_type, title, ch_config in db.fetchall():
        try:
            ch_config = json.loads(ch_config)
        except:
            print ("Unable to parse channel {}:{} config.".format(id_channel, title))
            continue
        ch_config.update({"title":title})
        if channel_type == PLAYOUT:
            config["playout_channels"][id_channel] = ch_config
        elif channel_type == INGEST:
            config["ingest_channels"][id_channel] = ch_config


def load_meta_types(db):
    global meta_types
    db.query("SELECT key, ns, editable, searchable, class, settings FROM meta_types")
    for key, ns, editable, searchable, meta_class, settings in db.fetchall():
        meta_type = MetaType(key)
        meta_type.namespace   = ns
        meta_type.editable    = bool(editable)
        meta_type.searchable  = bool(searchable)
        meta_type.meta_class  = meta_class
        meta_type.settings    = settings
        db.query("SELECT lang, alias, col_header FROM meta_aliases WHERE key=%s", [key])
        for lang, alias, col_header in db.fetchall():
            meta_type.aliases[lang] = alias, col_header
        meta_types[key] = meta_type
    return True



def load_storages(db):
    global storages
    db.query("SELECT id, title, protocol, path, login, password FROM storages")
    for id_storage, title, protocol, path, login, password in db.fetchall():
        storage = Storage(
            id=id_storage,
            title=title,
            protocol=protocol,
            path=path,
            login=login,
            password=password
            )
        storages.add(storage)


def load_all():
    logging.debug("Loading site configuration from DB", handlers=False)
    try:
        # This is the first time we are connecting DB so error handling should be here
        db = DB()
    except:
        log_traceback(handlers=False)
        critical_error("Unable to connect database", handlers=False)

    load_site_settings(db)
    load_meta_types(db)
    load_storages(db)
    messaging.configure()

load_all()
