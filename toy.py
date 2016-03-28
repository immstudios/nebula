#!/usr/bin/env python
import time

from nebula import *

def the_toy():
    dur = 0
    for asset in browse(id_folder=[1,3,4], genre="Horror"):
        print asset
        dur += asset.duration
    logging.info("total duration is", s2words(dur))


if __name__ == "__main__":
    print ""
    start_time = time.time()
    the_toy()
    logging.goodnews("Script executed in {:03f}s".format(time.time() - start_time))
