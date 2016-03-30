#!/usr/bin/env python
import time

from nebula import *

def the_toy():
    dur = 0
    count = 0
    for asset in get_assets(id_folder=[1,2,3]):
        dur += asset.duration
        count += 1
    logging.info("total duration of {} assets is".format(count), s2words(dur))


if __name__ == "__main__":
    print ""
    start_time = time.time()
    the_toy()
    logging.goodnews("Script executed in {:03f}s".format(time.time() - start_time))
