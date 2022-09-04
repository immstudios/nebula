#!/usr/bin/env python

import os
import time
import psycopg2

config = {}
for key, value in dict(os.environ).items():
    if key.lower().startswith("nebula_"):
        key = key.lower().replace("nebula_", "", 1)
        config[key] = value


class DB(object):
    def __init__(self, **kwargs):
        self.pmap = {
            "host": "db_host",
            "user": "db_user",
            "password": "db_pass",
            "database": "db_name",
        }

        self.settings = {
            key: kwargs.get(
                self.pmap[key], 
                config[self.pmap[key]]
            ) for key in self.pmap
        }

        self.conn = psycopg2.connect(**self.settings)
        self.cur = self.conn.cursor()

    def query(self, query, *args):
        self.cur.execute(query, *args)

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()


while True:
    try:
        db = DB()
        db.query("select value from settings where key = 'redis_host'")
    except Exception:
        print("Waiting for db")
    else:
        break
    time.sleep(1)

