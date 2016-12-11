from .core import *
from .core.base_objects import *
from .connection import *

__all__ = ["Asset", "Item", "Bin", "Event", "User"]

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
    @property
    def db(self):
        if not hasattr(self, "_db"):
            logging.debug("{} is opening DB connection.".format(self.__repr__().capitalize()))
            self._db = DB()
        return self._db

    def load(self, id):
        pass

    def save(self, **kwargs):
        if self.is_new:
            self._insert(**kwargs)
        else:
            self._update(**kwargs)
            self.invalidate()
        if self.text_changed:
            self.update_ft_index()
        self.db.commit()
        self.cache()
        self.text_changed = self.meta_changed = False

    def _insert(self):
        meta = json.dumps(self.meta)
        query = "INSERT INTO objects (object_type, meta) VALUES (%s, %s) RETURNING id"
        self.db.query(query, [self.object_type_id, meta])
        if not self.id:
            self["id"] = self.db.fetchall()[0][0]
            self.db.query("UPDATE objects SET meta=%s WHERE id=%s", [json.dumps(self.meta), self.id])

    def _update(self):
        assert id > 0
        meta = json.dumps(self.meta)
        query = "UPDATE objects SET meta=%s WHERE id=%s"
        self.db.query(query, [meta, self.id])

    def update_ft_index(self):
        self.db.query("DELETE FROM ft WHERE id=%s", [self.id])
        args = [(self.id, ft[word], word) for word in ft]
        tpls = ','.join(['%s'] * len(args))
        db.query("INSERT INTO ft (id, weight, value) VALUES {}".format(tpl), args)

    def cache(self):
        """Save object to cache"""
        #TODO

    def invalidate(self):
        """Invalidate all cache objects which references this one"""
        pass




class ObjectHelper(object):
    def __init__(self):
        self.classes = {}

    def __setitem__(self, key, value):
        self.classes[key] = value

    def invalidate(self, object_type, meta):
        obj = self.classes[object_type](meta=meta)
        obj.invalidate()

object_helper = ObjectHelper()







class Asset(AssetMixIn, ServerObject):
    pass


class Item(ItemMixIn, ServerObject):
    @property
    def asset(self):
        if not hasattr(self, "_asset"):
            if not self["id_asset"]:
                self._bin = False # Virtual items
            #TODO
        return self._asset

    @property
    def bin(self):
        if not hasattr(self, "_bin"):
            self._bin = Bin(self["id_bin"], db=self.db)

    @property
    def event(self):
        _bin = self.bin
        if not _bin:
            return False
        return _bin.event

    def invalidate(self):
        pass


class Bin(BinMixIn, ServerObject):

    def load_all(self):
        """Force load all items and their assets data"""
        db = self.db
        db.query("")
        for imeta, ameta in db.fetchall():
            pass #TODO

    def invalidate(self):
        pass

    @property
    def items(self):
        if not hasattr(self, "_items"):
            #TODO: load
            pass
        return self._items

    @property
    def event(self):
        pass


class Event(EventMixIn, ServerObject):
    @property
    def bin(self):
        if not hasattr(self, "_bin"):
            if not self["id_bin"]: # non-playout events
                self._bin = False
            #TODO
        return self._bin


class User(UserMixIn, ServerObject):
    pass


object_helper[ASSET] = Asset
object_helper[ITEM]  = Item
object_helper[BIN]   = Bin
object_helper[EVENT] = Event
object_helper[USER]  = User

