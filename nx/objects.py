from nebulacore import *
from nebulacore.base_objects import *

from .connection import *
from .server_object import *

__all__ = ["Asset", "Item", "Bin", "Event", "User", "anonymous"]


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
    table_name = "assets"
    db_cols = ["id_folder", "content_type", "media_type", "status", "version_of", "ctime", "mtime"]

    def invalidate(self):
        # Invalidate view count
        # Performance idea:
        #  - invalidate only if view is affected (folder changed, inserted...)
        for id_view in config["views"]:
            view = config["views"][id_view]
            for id_folder in view.get("folders"):
                if self["id_folder"] == id_folder:
                    logging.debug("Invalidating view count"+str(id_view))
                    cache.delete("view-count-"+str(id_view))
                    break


class Item(ItemMixIn, ServerObject):
    table_name = "items"
    db_cols = ["id_asset", "id_bin", "position"]
    defaults = {"id_asset" : 0, "position" : 0}

    @property
    def asset(self):
        if not hasattr(self, "_asset"):
            if not self["id_asset"]:
                self._asset =False # Virtual items
            #TODO: loading
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

    def __getitem__(self, key):
        if key in self.meta:
            return super(Item, self).__getitem__(key)
        return self.asset[key]



class Bin(BinMixIn, ServerObject):
    table_name = "bins"
    db_cols = ["bin_type"]

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
    table_name = "events"
    db_cols = ["id_channel", "start", "stop", "id_magic"]

    @property
    def bin(self):
        if not hasattr(self, "_bin"):
            if not self["id_bin"]: # non-playout events
                self._bin = False
            self._bin = Bin(self["id_bin"], db=self._db)
        return self._bin


class User(UserMixIn, ServerObject):
    table_name = "users"
    db_cols = ["login", "password"]

#
# Helpers
#


object_helper[ASSET] = Asset
object_helper[ITEM]  = Item
object_helper[BIN]   = Bin
object_helper[EVENT] = Event
object_helper[USER]  = User

anonymous = User(meta={
        "login" : "Anonymous"
    })
