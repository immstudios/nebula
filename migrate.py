#!/usr/bin/env python
import time
import json

from nebula import *

start_time = time.time()

#
# Open dump
#

with open("dump.json") as f:
    data = json.load(f)

#
# Site settings
#

folders = [
    [1, "Movie"],
    [2, "Serie"],
    [3, "Trailer"],
    [4, "Jingle"],
    [5, "Music"],
    [6, "News"],
    [7, "Fill"],
    [8, "Template"],
    [9, "Commercial"],
    [10, "Incomming"]
]

origins = [
    [1, "Production"],
    [2, "Playout 1"]
]

meta_types = [
]


#
# Delete everything first
#

db = DB()
db.query("""
    TRUNCATE TABLE
        folders,
        assets,
        items,
        events,
        bins,
        origins
    RESTART IDENTITY;""")
db.commit()

#
# Settings tables deployment
#

for id, title in origins:
    db.query("INSERT INTO origins (id, title) VALUES (%s, %s)", [id, title])

for id, title in folders:
    db.query("INSERT INTO folders (id, title) VALUES (%s, %s)", [id, title])

db.commit()

#
# Object transfer
#

for asset_data in data["assets"]:
    if asset_data["origin"] != "Production":
        continue

    asset = Asset(meta=asset_data, db=db)
    asset["id"] = False
    asset["id_origin"] = 1
    asset.save()

logging.goodnews("Nebula migration completed in {:03f} seconds".format(time.time() - start_time))
