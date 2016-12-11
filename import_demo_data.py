#!/usr/bin/env python

from nebula import *

demo_movies = "support/demo-movies.mjson"

def import_data(data_file):
    db = DB()
    with open(data_file) as f:
        for row in f.readlines():
            meta = json.loads(row)
            asset = Asset(meta=meta, db=db)
            asset.save()

if __name__ == "__main__":
    import_data(demo_movies)
