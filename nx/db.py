import time
from .core import *

try:
    import psycopg2
except ImportError:
    log_traceback("Import error")
    critical_error("Unable to import psycopg2")

__all__ = ["DB"]

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
        else:
            raise psycopg2.OperationalError
        self.cur = self.conn.cursor()

    def sanit(self, instr):
        try:
            return str(instr).replace("''","'").replace("'","''").decode("utf-8")
        except:
            return instr.replace("''","'").replace("'","''")

    def lastid (self):
        self.query("SELECT LASTVAL()")
        return self.fetchall()[0][0]

