#!/usr/bin/env python
from __future__ import print_function

from nebula import *




def format_status(key, asset):
    colored = "\033[{}m{:<8}\033[0m"
    return {
            OFFLINE  : colored.format(31, "OFFLINE"),
            ONLINE   : colored.format(32, "ONLINE"),
            CREATING : colored.format(33, "CREATING"),
            TRASHED  : colored.format(34, "TRASHED"),
            ARCHIVED : colored.format(34, "ARCHIVE"),
            RESET    : colored.format(33, "RESET"),
        }[asset[key]]

def format_title(key, asset):
    return "{:<30}".format(asset[key])

formats = {
        "id" : lambda key, asset: "{:<5}".format(asset[key]),
        "status" : format_status,
        "title" : lambda key, asset: "{:<24}".format(asset[key]),
    }




cols = ["id", "status", "title", "ctime", "mtime", "video/aspect_ratio"]

print()
print()

for response, asset in get_objects(Asset, order="id DESC"):

    l = ""
    for key in cols:
        l+= " " + str(formats[key](key, asset) if key in formats else asset.show(key))
    l+="\n"
    l=l.lstrip()

    try:
        sys.stdout.write(l)
        sys.stdout.flush()
    except IOError:
        pass
