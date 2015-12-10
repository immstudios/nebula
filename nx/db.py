import time
from .core import *

try:
    import psycopg2
except ImportError:
    log_traceback()
    critical_error("Unable to import psycopg2")

__all__ = ["DB"]


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
                self.conn = psycopg2.connect(database = self.kwargs.get('db_name', False) or config['db_name'], 
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
