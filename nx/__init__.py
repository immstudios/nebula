from .core import *
from .db import DB


def reconfigure():
    logging.info("Loading configuration...")
    db = DB()

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


    for obj in [messaging, meta_types]:
        obj.configure()
    
    ##
    # Storages
    ##

    storages.clear()
    db.query("SELECT id_storage, title, protocol, path, login, password FROM nx_storages")
    for id_storage, title, protocol, path, login, password in db.fetchall():
        storage = Storage()
        storage["id_storage"] = id_storage
        storage["title"]      = title
        storage["protocol"]   = protocol
        storage["path"]       = path
        storage["login"]      = login
        storage["password"]   = password
        storages.add(storage)

    logging.goodnews("Nebula configuration updated")

#reconfigure()




