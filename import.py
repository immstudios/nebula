#!/usr/bin/env python3

import os
import json
import time
import sqlite3

from pprint import pprint
from nebula import *

site_name = config["site_name"]
data_url = "https://{}.nebulabroadcast.com/dump/dump.db".format(site_name)
data_path = "/tmp/{}.db".format(site_name)

def do_download():
    os.system("curl {} -o {}".format(data_url, data_path))

if not os.path.exists(data_path) or os.path.getmtime(data_path) < time.time() - 3600:
    do_download()

#
# Lots of magic numbers were changed between v4 and v5. Sorry :-/
#

folder_map = {
        1 : 1,   # movie
        2 : 2,   # serie
        3 : 6,   # trailer
        4 : 7,
        5 : 4,   # song
        6 : 3,
        7 : 5,   # fill
        8 : 8,   # templates
        10 : 12, # incomming
        11 : 9,  # reklama
        12 : 10, # teleshopping
    }

content_type_map = {
        2 : AUDIO,
        1 : VIDEO,
        3 : IMAGE,
        0 : TEXT,
    }

media_type_map = {
        1 : VIRTUAL,
        0 : FILE,
    }

def parse_rights(value):
    return value #TODO

meta_keys = {
    "id_bin"                    : lambda x: int(x),
    "id_asset"                  : lambda x: int(x),
    "is_optional"               : lambda x: int(x),
    "position"                  : lambda x: int(x),
    "item_role"                 : None,
    "run_mode"                  : lambda x: int(x),
    "bin_type"                  : lambda x: int(x),
    "id_channel"                : lambda x: int(x),
    "color"                     : lambda x: int(x.lstrip("#"), 16),
    "stop"                      : lambda x: int(x),
    "start"                     : lambda x: int(x),
    "dramatica/config"          : None,
    "id_magic"                  : lambda x: int(x),
    "is_optional"               : lambda x: int(x),
    "login"                     : None,
    "password"                  : None,
    "is_admin"                  : lambda x: {True : True, 1 : True, "true" : True}.get(x, False),
    "full_name"                 : None,
    "album"                     : None,
    "album/disc"                : lambda x: int(x),
    "album/track"               : lambda x: int(x),
#TODO    "contains/cg_text" : None,
#TODO    "contains/nudity" : None,
    "content_type"              : lambda x: content_type_map[x],
    "ctime"                     : lambda x: int(x),
    "description"               : None,
    "description/original"      : None,
    "director"                  : None,
    "duration"                  : lambda x: float(x),
    "file/format"               : None,
    "file/mtime"                : None,
    "file/size"                 : None,
    "genre"                     : None,
    "genre/music" : -1,
    "has_thumbnail"             : lambda x: int(x),
    "id_folder"                 : lambda x: folder_map[x],
    "id_object"                 : "id",
    "id_storage"                : lambda x: int(x),
    "identifier/guid"           : None,
    "identifier/vimeo"          : None,
    "identifier/youtube"        : None,
    "mark_in"                   : None,
    "mark_out"                  : None,
    "media_type"                : lambda x: media_type_map[x],
    "mtime"                     : None,
    "path"                      : None,
    "promoted"                  : None,
    "qc/analyses" : -1,
    "qc/report" : -1,
    "qc/silence" : -1,
    "qc/state"                  : None,
    "rights"                    : None,
    "role/composer"             : None,
    "role/director"             : None,
    "role/performer"            : None,
    "series/episode"            : None,
    "series/season"             : None,
    "source"                    : None,
    "source/author"             : None,
    "source/url"                : None,
    "status"                    : None,
    "subject"                   : "keywords",
    "title"                     : None,
    "title/original"            : None,
    "title/subtitle"            : "subtitle",
    "version_of"                : lambda x: x or 0,

    "audio/bpm"                 : None,
    "audio/gain/mean"           : None,
    "audio/gain/peak"           : None,
    "audio/r128/i"              : None,
    "audio/r128/lra"            : None,
    "audio/r128/lra/l"          : None,
    "audio/r128/lra/r"          : None,
    "audio/r128/lra/t"          : None,
    "audio/r128/t"              : None,
    "video/aspect_ratio"        : None,
    "video/codec"               : None,
    "video/color_range"         : None,
    "video/color_space"         : None,
    "video/fps"                 : None,
    "video/height"              : None,
    "video/pixel_format"        : None,
    "video/width"               : None,


    "broker/started/1" : -1,
    "broker/started/2" : -1,


    "origin" : -1,
    "v3/path" : -1,
    "v3/id" : -1,
    "title/series" : "serie",
    "v3/storage" : -1,
    "id_playout/1" : -1,
    "identifier/main" : None,
    "qc/analyses" : -1,
    "qc/silence" : -1,
    "date" : -1,
    "logo" : -1,
    "date/valid" : -1,
    "subclips" : -1,
    "format" : "editorial_format",
    "commercials/client" : -1,
    "notes" : None,
    "meta_probed" : -1,
    "identifier/atmedia" : -1,
    "rundown_broadcast" : -1,
    "rundown_bin" : -1,
    "rundown_row" : -1,
    "rundown_scheduled" : -1,
    "locked" : -1,
    "can/job_control" : parse_rights,
    "can/asset_edit" : parse_rights,
    "can/mcr" : parse_rights,
    "can/service_control" : parse_rights,
    "can/rundown_view" : parse_rights,
    "can/asset_create" :parse_rights,
    "can/cg" : parse_rights,
    "can/rundown_edit" : parse_rights,
    "can/scheduler_edit" : parse_rights,
    "can/scheduler_view" : parse_rights,
    "can/export" : parse_rights,
}


OBJECT_TYPES = [
        ["assets", Asset],
        ["items", Item],
        ["bins", Bin],
        ["events", Event],
        ["users", User]
    ]

class SourceDB(object):
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def query(self, *args):
        return self.cursor.execute(*args)

    def commit(self):
        self.connection.commit()

    def fetchall(self):
        return self.cursor.fetchall()


def check_keys():
    sdb = SourceDB(data_path)
    ignore = []
    for table_name, object_type in OBJECT_TYPES:
        sdb.query("select data from {}".format(table_name))
        for data, in sdb.fetchall():
            data = json.loads(data)
            for key in data.keys():
                if key in meta_keys or key in ignore:
                        continue
                logging.warning("Unknown key: {}".format(key))
                ignore.append(key)




class ImportObject(object):
    def __init__(self, meta):
        self.meta = meta

    def __getitem__(self, key):
        return self.meta.get(key, False)

    def translate(self):
        if self["origin"] and self["origin"] != "Production":
            return False
        result = {}

        for key in meta_keys:
            conv = meta_keys[key]


            if not key in self.meta:
                if key in ["version_of", "status"]:
                    self.meta[key] = 0
                else:
                    continue

            if callable(conv):
                result[key] = conv(self[key])
            elif type(conv) == str:
                result[conv] = self[key]
            elif conv is None:
                result[key] = self[key]
            else:
                continue

        return result


if __name__ == "__main__":
    db = DB()

    if "--full" in sys.argv:
        logging.info("Deleting old data")
        db.query("TRUNCATE TABLE assets, events, bins, items, users, jobs, asrun RESTART IDENTITY")
        db.commit()

    for table_name, ObjectClass in [
                ["assets", Asset],
                ["events", Event],
                ["bins", Bin],
                ["items", Item],
                ["users", User],
            ]:

        sdb = SourceDB(data_path)

        db.query("SELECT meta->>'mtime' FROM {} ORDER BY meta->>'mtime' DESC LIMIT 1".format(table_name))
        try:
            last_mtime = db.fetchall()[0][0]
        except:
            last_mtime = 0

        i = 0
        sdb.query("SELECT id, data FROM {} WHERE mtime > ? ORDER BY mtime ASC".format(table_name), [last_mtime])
        for id, data in sdb.fetchall():
            src = ImportObject(json.loads(data))

            translated = src.translate()
            if not translated:
                continue

            obj = ObjectClass(meta=translated, db=db)
            obj.is_new = True

            try:
                obj.save(commit=False, set_mtime=False)
            except IntegrityError:
                log_traceback()
                print (data)
                print (translated)
                logging.warning("Integrity error: {} : {}".format(table_name, id))
                #TODO: Update newer
                sys.exit(0)
                db.commit()
            except Exception:
                log_traceback()
                logging.error(str(translated))
                continue

            #logging.info("Importing {}".format(table_name))

            i+=1
            if i % 1000 == 0:
                logging.debug("{} {} imported".format(i, table_name))
                db.commit()

        db.commit()

        db.query("SELECT setval(pg_get_serial_sequence('{}', 'id'), coalesce(max(id),0) + 1, false) FROM {};".format(table_name, table_name))
        logging.debug("serial reset >>", (db.fetchall()))
        db.commit()


    sys.exit(0)
