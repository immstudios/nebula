#!/usr/bin/env python

import sys

from nebula import *

dump_path = "/opt/nebula-setup/dump.json"
dump_data = json.load(open(dump_path))


def asset_transform(meta):
    if "id_object" in meta:
        meta["id"] = int(meta["id_object"])
        del(meta["id_object"])
    return meta


def import_objects(data):
    groups = {
            "assets" : [Asset, asset_transform],
        }
    for group in groups:
        obj_class, transform = groups[group]
        for meta in data[group]:
            meta = transform(meta)
            obj = obj_class(meta=meta)
            obj.is_new = True

            print obj

if __name__ == "__main__":
    import_objects(dump_data)
