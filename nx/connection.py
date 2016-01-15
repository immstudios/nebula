import psycopg2
from .core import *

__all__ = ["DB", "cache", "Cache"]

##
# Database
##

class BaseDB(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
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
    def _connect(self):
        i = 0
        while i < 3:
            try:
                self.conn = psycopg2.connect(
                    database = self.kwargs.get('db_name', False) or config['db_name'],
                    host     = self.kwargs.get('db_host', False) or config['db_host'],
                    user     = self.kwargs.get('db_user', False) or config['db_user'],
                    password = self.kwargs.get('db_pass', False) or config['db_pass']
                    )
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

#######################################################################################################
## Cache

import pylibmc

class Cache():
    def __init__(self):
        if "cache_host" in config:
            self.configure()

    def configure(self):
        self.site = config["site_name"]
        self.host = config["cache_host"]
        self.port = config["cache_port"]
        self.cstring = '%s:%s'%(self.host,self.port)
        self.pool = False
        self.connect()

    def connect(self):
        self.conn = pylibmc.Client([self.cstring])
        self.pool = False

    def load(self, key):
        if config.get("mc_thread_safe", False):
            return self.tload(key)

        key = "{}_{}".format(self.site,key)
        try:
            result = self.conn.get(key)
        except pylibmc.ConnectionError:
            self.connect()
            result = False
        return result

    def save(self, key, value):
        if config.get("mc_thread_safe", False):
            return self.tsave(key, value)

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
            critical_error ("Memcache save failed. This should never happen. Check MC server")
            sys.exit(-1)
        return True

    def delete(self,key):
        if config.get("mc_thread_safe", False):
            return self.tdelete(key)
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
            critical_error ("Memcache delete failed. This should never happen. Check MC server")
            sys.exit(-1)
        return True


    def tload(self, key):
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

    def tsave(self, key, value):
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
                critical_error ("Memcache save failed. This should never happen. Check MC server")
                sys.exit(-1)
        self.pool.relinquish()
        return True

    def tdelete(self,key):
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
                critical_error ("Memcache delete failed. This should never happen. Check MC server")
                sys.exit(-1)
        self.pool.relinquish()
        return True


cache = Cache()
