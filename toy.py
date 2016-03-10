#!/usr/bin/env python
import time
import json
from nebula import *


def the_toy():
    db = DB()
    db.query("SELECT metadata, ft_index FROM assets")
    for meta, idx in db.fetchall():
        print meta["title"]
        print idx
        print ""


if __name__ == "__main__":
    start_time = time.time()
    the_toy()
    logging.goodnews("Script executed in {:03f}s".format(time.time() - start_time))
