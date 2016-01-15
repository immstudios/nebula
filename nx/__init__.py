from .core import *
from .connection import *


def load_site_settings(db):
    global config
    config["playout_channels"] = {}
    config["ingest_channels"] = {}
    config["views"] = {}

    db.query("SELECT key, value FROM nx_settings")
    for key, value in db.fetchall():
        config[key] = value

    db.query("SELECT id_view, config FROM nx_views")
    for id_view, view_config in db.fetchall():
        view_config = ET.XML(view_config)
        view = {}
        for elm in ["query", "folders", "origins", "media_types", "content_types", "statuses"]:
            try:
                view[elm] = view_config.find(elm).text.strip()
            except:
                continue
        config["views"][id_view] = view

    db.query("SELECT id_channel, channel_type, title, config FROM nx_channels")
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
    db.query("SELECT namespace, tag, editable, searchable, class, default_value,  settings FROM nx_meta_types")
    for ns, tag, editable, searchable, class_, default, settings in db.fetchall():
        meta_type = MetaType(tag)
        meta_type.namespace  = ns
        meta_type.editable   = bool(editable)
        meta_type.searchable = bool(searchable)
        meta_type.class_     = class_
        meta_type.default    = default
        meta_type.settings   = json.loads(settings)
        db.query("SELECT lang, alias, col_header FROM nx_meta_aliases WHERE tag='{0}'".format(tag))
        for lang, alias, col_header in db.fetchall():
            meta_type.aliases[lang] = alias, col_header
        meta_types[tag] = meta_type
    return True


def load_storages(db):
    global storages
    db.query("SELECT id_storage, title, protocol, path, login, password FROM nx_storages")
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
    load_meta_types(db)
    load_storages(db)

    cache.configure()
    messaging.configure()

load_all()
