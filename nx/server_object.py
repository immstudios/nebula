from .core import *
from .core.base_objects import BaseObject
from .connection import *

__all__ = ["ServerObject"]

def create_ft_index(meta):
    ft = {}
    for key in meta:
        if not key in meta_types:
            continue
        weight = meta_types[key]["fulltext"]
        if not weight:
            continue
        for word in slugify(meta[key], make_set=True, min_length=3):
            if not word in ft:
                ft[word] = weight
            else:
                ft[word] = max(ft[word], weight)
    return ft


class ServerObject(BaseObject):
    def __init__(self, id=False, **kwargs):
        super(ServerObject, self).__init__(id, **kwargs)
        if "db" in kwargs:
            self._db = kwargs["db"]

    @property
    def db(self):
        if not hasattr(self, "_db"):
            logging.debug("{} is opening DB connection".format(self))
            self._db = DB()
        return self._db

    def load(self, id):
        key = str(self.object_type_id) + "-" + str(id)
        try:
            self.meta = json.loads(cache.load(key))
            return True
        except Exception:
            pass
        logging.debug("Loading {} ID:{} from DB".format(self.__class__.__name__, id))
        db = self.db
        db.query("SELECT meta FROM {} WHERE id = {}".format(self.table_name, id))
        try:
            self.meta = db.fetchall()[0][0]
        except IndexError:
            logging.error("Unable to load {} ID:{}. Object does not exist".format(self.__class__.__name__, id))
            return False

    def save(self, **kwargs):
        super(ServerObject, self).save(**kwargs)
        is_new = self.is_new
        if is_new:
            self._insert(**kwargs)
        else:
            self._update(**kwargs)
            self.invalidate()
        if self.text_changed or is_new:
            self.update_ft_index(is_new)
        if kwargs.get("commit", True):
            self.db.commit()
        self.cache()
        self.text_changed = self.meta_changed = False

    def _insert(self, **kwargs):
        meta = json.dumps(self.meta)
        cols = []
        vals = []
        if self.id:
            cols.append("id")
            vals.append(self.id)
        for col in self.db_cols:
            cols.append(col)
            vals.append(self[col])
        if self.id:
            cols.append("meta")
            vals.append(json.dumps(self.meta))

        if cols:
            query = "INSERT INTO {} ({}) VALUES ({}) RETURNING id".format(
                        self.table_name,
                        ", ".join(cols),
                        ", ".join(["%s"]*len(cols))
                    )
        else:
            query = "INSERT INTO {} DEFAULT VALUES RETURNING id".format(self.table_name)
        self.db.query(query, vals)

        if not self.id:
            self["id"] = self.db.fetchone()[0]
            self.db.query(
                    "UPDATE {} SET meta=%s WHERE id=%s".format(self.table_name),
                    [json.dumps(self.meta), self.id]
                )


    def _update(self, **kwargs):
        assert id > 0
        cols = ["meta"]
        vals = [json.dumps(meta)]

        for col in self.db_cols:
            cols.append(col)
            vals.append(self[col])

        meta = json.dumps(self.meta)
        query = "UPDATE {} SET {} WHERE id=%s".format(
                table_name,
                ", ".join(["{}=%s".format(key) for key in cols])
            )
        self.db.query(query, vals+[self.id])


    def update_ft_index(self, is_new=False):
        if not is_new:
            self.db.query("DELETE FROM ft WHERE object_type=%s AND id=%s", [self.object_type_id, self.id])
        ft = create_ft_index(self.meta)
        if not ft:
            return
        args = [(self.id, self.object_type_id, ft[word], word) for word in ft]
        tpls = ','.join(['%s'] * len(args))
        self.db.query("INSERT INTO ft (id, object_type, weight, value) VALUES {}".format(tpls), args)


    @property
    def cache_key(self):
        if not self.id:
            return False
        return str(self.object_type_id) + "-" + str(self.id)

    def cache(self):
        """Save object to cache"""
        cache_key = self.cache_key
        if not cache_key:
            return False
        cache.save(cache_key, json.dumps(self.meta))

    def invalidate(self):
        """Invalidate all cache objects which references this one"""
        pass
