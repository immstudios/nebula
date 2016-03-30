#!/usr/bin/env python

import sys

from nebula import *

dump_path = "../dump.json"
dump_data = json.load(open(dump_path))


def asset_transform(meta):

    # Keep just online videos

    if meta["content_type"] != 1:
        return None

    if meta["status"] == 3:
        return None

    if meta["origin"] != "Production":
        return None

    # Key rename

    for old_key, new_key in [
                ["id_object", "id"],
                ["title/subtitle", "subtitle"],
                ["genre/music", "genre"],
                ["subject", "keywords"],
                ["meta_probed", None],
                ["has_thumbnail", None],
                ["id_playout/1", None],
            ]:

        if old_key in meta:
            if new_key:
                meta[new_key] = meta[old_key]
            del(meta[old_key])

    # Content alert

    content_alert = []
    for tag in ["cg_text", "nudity"]:
        k = "contains/{}".format(tag)
        if k in meta:
            content_alert.append(tag)
            del(meta[k])
    if content_alert:
        meta["cotent_alert"] = content_alert

    # Genre translation

    genre_translation = {
        'Alt rock': 'Alternative',
        'Arts': 'Arts',
        'Comedy': 'Comedy',
        'Drama': 'Drama',
        'Electronic': 'Electronic',
        'Emo': 'Alternative',
        'Erotic': 'Erotica',
        'Hip Hop': 'Hip Hop',
        'Horror': 'Horror',
        'Metal': 'Metal',
        'Pop': 'Pop',
        'Rock': 'Rock',
        'Social': 'Social',
        'Technology': 'Technology'
    }

    if "genre" in meta:
        meta["genre"] = genre_translation.get(meta["genre"])

    return meta





def import_objects(data):
    groups = {
            "assets" : [Asset, asset_transform],
        }

    for group in groups:
        obj_class, transform = groups[group]
        for meta in data[group]:
            meta = transform(meta)
            if not meta:
                continue
            obj = obj_class(meta=meta)
            obj.is_new = True
            obj.save()

if __name__ == "__main__":
    import_objects(dump_data)
