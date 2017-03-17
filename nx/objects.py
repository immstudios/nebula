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
            if not self.meta.get("id_asset", False):
                self._asset = False # Virtual items
            else:
                self._asset = Asset(self["id_asset"], db=self._db) or False
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


class Bin(BinMixIn, ServerObject):
    table_name = "bins"
    db_cols = ["bin_type"]

    def invalidate(self):
        pass

    @property
    def items(self):
        if not hasattr(self, "_items"):
            self.db.query("SELECT meta FROM items WHERE id_bin=%s ORDER BY position ASC", [self.id])
            self._items = [Item(meta=meta, db=self.db) for meta, in self.db.fetchall()]
        return self._items

    @property
    def event(self):
        if not hasattr(self, "_event"):
            self.db.query("SELECT meta FROM events WHERE id_magic=%s", [self.id]) #TODO: playout only
            try:
                self._event = Event(meta=self.db.fetchall()[0][0])
            except Exception:
                log_traceback()
                self._event = False
        return self._event

    def delete_children(self):
        for item in self.items:
            item.delete()

    def save(self, **kwargs):
        duration = 0
        for item in self.items:
            duration += item.duration
        self["duration"] = duration
        super(Bin, self).save(**kwargs)


class Event(EventMixIn, ServerObject):
    table_name = "events"
    db_cols = ["id_channel", "start", "stop", "id_magic"]

    @property
    def bin(self):
        if not hasattr(self, "_bin"):
            if not self["id_bin"]: # non-playout events
                self._bin = False
            else:
                logging.debug("Loading bin ID {} of {} from DB".format(self["id_bin"], self))
                self._bin = Bin(self["id_bin"], db=self.db)
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
