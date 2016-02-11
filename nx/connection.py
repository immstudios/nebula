import time
from .core import *

try:
    import psycopg2
except ImportError:
    log_traceback("Import error")
    critical_error("Unable to import psycopg2")

try:
    import pylibmc
except ImportError:
    log_traceback("Import error")
    critical_error("Unable to import pylibmc")

__all__ = ["DB", "cache", "Cache"]

##
# Database
##

class BaseDB(object):
    pmap = {}

    def __init__(self, **kwargs):
        self.settings = {
            key : kwargs.get(self.pmap[key], config[self.pmap[key]]) for key in self.pmap
            }
        self._connect()

    def _connect(self):
        pass

    def query(self, q, *args):
        self.cur.execute(q,*args)

    def fetchall(self):
        return self.cur.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __len__(self):
        return True


class DB(BaseDB):
    pmap = {
        "host" : "db_host",
        "user" : "db_user",
        "password" : "db_pass",
        "database" : "db_name",
        }

    def _connect(self):
        i = 0
        while i < 3:
            try:
                self.conn = psycopg2.connect(**self.settings)
            except psycopg2.OperationalError:
                time.sleep(1)
                i+=1
                continue
            else:
                break
        self.cur = self.conn.cursor()

    def sanit(self, instr):
        try:
            return str(instr).replace("''","'").replace("'","''").decode("utf-8")
        except:
            return instr.replace("''","'").replace("'","''")

    def lastid (self):
        self.query("select lastval()")
        return self.fetchall()[0][0]

##
# Cache
##

class Cache():
    def __init__(self):
        if "cache_host" in config:
            self.configure()

    def configure(self):
        self.site = config["site_name"]
        self.host = config["cache_host"]
        self.port = config["cache_port"]
        self.cstring = "{}:{}".format(self.host, self.port)
        self.pool = False
        self.connect()

    def connect(self):
        self.conn = pylibmc.Client([self.cstring])
        self.pool = False

    def load(self, key):
        if config.get("mc_thread_safe", False):
            return self.threaded_load(key)

        key = "{}_{}".format(self.site, key)
        try:
            result = self.conn.get(key)
        except pylibmc.ConnectionError:
            self.connect()
            result = False
        return result

    def save(self, key, value):
        if config.get("mc_thread_safe", False):
            return self.threaded_save(key, value)

        key = "{}_{}".format(self.site, key)
        for i in range(10):
            try:
                self.conn.set(key, str(value))
                break
            except:
                log_traceback("Cache save failed ({})".format(key))
                time.sleep(.3)
                self.connect()
        else:
            critical_error("Memcache save failed. This should never happen. Check MC server")
            sys.exit(-1)
        return True

    def delete(self,key):
        if config.get("mc_thread_safe", False):
            return self.threaded_delete(key)
        key = "{}_{}".format(self.site, key)
        for i in range(10):
            try:
                self.conn.delete(key)
                break
            except:
                log_traceback("Cache delete failed ({})".format(key))
                time.sleep(.3)
                self.connect()
        else:
            critical_error("Memcache delete failed. This should never happen. Check MC server")
            sys.exit(-1)
        return True

    def threaded_load(self, key):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        key = "{}_{}".format(self.site, key)
        result = False
        with self.pool.reserve() as mc:
            try:
                result = mc.get(key)
            except pylibmc.ConnectionError:
                self.connect()
                result = False
        self.pool.relinquish()
        return result

    def threaded_save(self, key, value):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        key = "{}_{}".format(self.site, key)
        with self.pool.reserve() as mc:
            for i in range(10):
                try:
                    mc.set(key, str(value))
                    break
                except:
                    log_traceback("Cache save failed ({})".format(key))
                    time.sleep(.3)
                    self.connect()
            else:
                critical_error("Memcache save failed. This should never happen. Check MC server")
                sys.exit(-1)
        self.pool.relinquish()
        return True

    def threaded_delete(self,key):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        key = "{}_{}".format(self.site, key)
        with self.pool.reserve() as mc:
            for i in range(10):
                try:
                    mc.delete(key)
                    break
                except:
                    log_traceback("Cache delete failed ({})".format(key))
                    time.sleep(.3)
                    self.connect()
            else:
                critical_error("Memcache delete failed. This should never happen. Check MC server")
                sys.exit(-1)
        self.pool.relinquish()
        return True

cache = Cache()
