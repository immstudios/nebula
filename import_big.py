#!/usr/bin/env python

import os
import sys
import json

from nebula import *

def do_import(data_path):
    start_time = time.time()
    count = 0
    db = DB()
    for line in open(data_path):
        count += 1
        asset_meta = json.loads(line)
        asset = Asset(meta=asset_meta, db=db)
        asset["origin"] = "Production"
        asset["status"] = ONLINE
        asset["content_type"] = AUDIO
        asset["media_type"] = FILE
        asset.save()
        if count % 10000 == 0:
            logging.debug("{} assets imported".format(count))
    logging.goodnews("{} assets imported in {:02f} seconds".format(count, time.time() - start_time))

if __name__ == "__main__":
    data_path = "/opt/data.txt"
    do_import(data_path)
