from .core import *
from .objects import *
from .db import *


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
        settings = XML(settings)
        view = {}
        for elm in ["query", "folders", "origins", "media_types", "content_types", "statuses"]:
            try:
                view[elm] = settings.find(elm).text.strip()
            except:
                continue
        config["views"][id_view] = view

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
    db.query("SELECT key, ns, ft, class, default_value, settings FROM meta_types")
    for key, ns, ft, class_, default, settings in db.fetchall():
        meta_type = MetaType(key)
        meta_type.ns = ns
        meta_type.ft = bool(searchable)
        meta_type.class_ = class_
        meta_type.default = default
        meta_type.settings = settings
        meta_types[tag] = meta_type
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
    db = DB()
    load_site_settings(db)
#    load_meta_types(db)
    load_storages(db)
    messaging.configure()

load_all()
