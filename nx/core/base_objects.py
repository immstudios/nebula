from .common import *
from .constants import *
from .metadata import meta_types

__all__ = ["BaseObject", "BaseAsset", "BaseItem", "BaseBin", "BaseEvent"]

class BaseObject(object):
    object_type = "asset"

    def __init__(self, *args, **kwargs):
        self.id = int(args[0]) if args else False

        self.ns_prefix = self.object_type[0]
        self.ns_tags   = meta_types.ns_tags(self.ns_prefix)
        self.meta = {}

        self._loaded = False
        self._db = kwargs.get("db", False)
        self._cache = kwargs.get("cache", False)

        if "from_data" in kwargs:
            assert hasattr(kwargs["from_data"], "keys")
            self.meta = kwargs["from_data"]
            self.id = self.meta.get("id_object", False)
            self._loaded = True
        else:
            if self.id:
                if self._load():
                    self._loaded = True
            else:
                self._new()

    def keys(self):
        return self.meta.keys()

    def id_object_type(self):
        return OBJECT_TYPES[self.object_type]

    def _new(self):
        self.meta = {}

    def _load(self):
        pass

    def _save(self,**kwargs):
        pass

    def save(self, **kwargs):
        if kwargs.get("set_mtime", True):
            self["mtime"] = int(time.time())
        return self._save(**kwargs)

    def delete(self):
        pass

    def __getitem__(self, key):
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]

    def __setitem__(self, key, value):
        key = key.lower().strip()
        if value or type(value) in [float, int, bool]:
            self.meta[key] = meta_types.format(key,value)
        else:
            del self[key] # empty strings
        return True

    def __delitem__(self, key):
        key = key.lower().strip()
        if key in meta_types and meta_types[key].namespace == self.object_type[0]:
            return
        if not key in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        if self.id:
            iid = "{} ID:{}".format(self.object_type, self.id)
        else:
            iid = "new {}".format(self.object_type)
        try:
            title = self["title"] or ""
            if title:
                title = " ({})".format(title)
            return "{}{}".format(iid, title)
        except:
            return iid

    def __len__(self):
        return self._loaded








class BaseAsset(BaseObject):
    object_type = "asset"

    def _new(self):
        self.meta = {
        }

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return self["mark_in"]

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return self["mark_out"]

    @property
    def file_path(self):
        try:
            return os.path.join(storages[self["id_storage"]].local_path, self["path"])
        except:
            return "" # Yes. empty string. keep it this way!!! (because of os.path.exists and so on)

    @property
    def duration(self):
        dur = float(self.meta.get("duration",0))
        mki = float(self.meta.get("mark_in" ,0))
        mko = float(self.meta.get("mark_out",0))
        if not dur: return 0
        if mko > 0: dur -= dur - mko
        if mki > 0: dur -= mki
        return dur



class BaseItem(BaseObject):
    object_type = "item"
    _asset = False

    def _new(self):
        self["id_bin"]    = False
        self["id_asset"]  = False
        self["position"]  = 0

    def __getitem__(self, key):
        key = key.lower().strip()
        if key == "id_object":
            return self.id
        if not key in self.meta :
            if self.asset:
                return self.asset[key]
            else:
                return False
        return self.meta[key]

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return float(self["mark_in"])

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return float(self["mark_out"])

    @property
    def asset(self):
        pass

    @property
    def bin(self):
        pass

    @property
    def event(self):
        pass

    @property
    def duration(self):
        """Final duration of the item"""
        if self["id_asset"]:
            dur = self.asset["duration"]
        elif self["duration"]:
            dur = self["duration"]
        else:
            return self.mark_out() - self.mark_in()
        if not dur:
            return 0
        mark_in  = self.mark_in()
        mark_out = self.mark_out()
        if mark_out > 0: dur -= dur - mark_out
        if mark_in  > 0: dur -= mark_in
        return dur



class BaseBin(BaseObject):
    object_type = "bin"
    items = []

    def _new(self):
        self.meta = {}
        self.items = []


class BaseEvent(BaseObject):
    object_type = "event"
    _bin        = False
    _asset      = False

    def _new(self):
        self["start"]      = 0
        self["stop"]       = 0
        self["id_channel"] = 0
        self["id_magic"]   = 0
