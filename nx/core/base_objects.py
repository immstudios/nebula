from .common import *
from .constants import *
from .metadata import meta_types

__all__ = ["BaseObject", "BaseAsset", "BaseItem", "BaseBin", "BaseEvent", "BaseUser"]

class BaseObject(object):
    def __init__(self, id=False, **kwargs):
        self.is_new = True
        self.meta = {}
        meta = kwargs.get("meta", {})
        for key in meta:
            self.meta[key] = meta[key]
        self._db = kwargs.get("db", False)
        if "id" in self.meta:
            self.is_new = False
        else:
            if id:
                self.load(id)
                self.is_new = False
            else:
                self.new()
                self.is_new = True

    @property
    def id(self):
        return self.meta.get("id", False)

    @property
    def object_type(self):
        return self.__class__.__name__.lower()

    def keys(self):
        return self.meta.keys()

    def __getitem__(self, key):
        return self.meta.get(key. meta_types[key].default)

    def __setitem__(self, key, value):
        self.meta[key] = meta_types[key].validate(value)
        return True

    def load(self, id):
        pass

    def new(self):
        #TODO: Default metadata here. At least origin and asset_type must be specified by user
        pass

    def save(self, **kwargs):
        if kwargs.get("set_mtime", True):
            self["mtime"] = int(time.time())
        self._save(**kwargs)

    def delete(self, **kwargs):
        assert self.id > 0, "Unable to delete unsaved asset"
        self._delete(**kwargs)

    def __delitem__(self, key):
        if key in self.db_map:
            return
        if not key in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        if self.id:
            result = "{} ID:{}".format(object_type, self.id)
        else:
            result = "new {}".format(object_type)
        title =  self.meta.get("title", "")
        if title:
            result += " ({})".format(title)
        return result

    def __len__(self):
        return bool(self.meta)

    def show(self, key):
        return meta_types.humanize(key, self[key])






class BaseAsset(BaseObject):
    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return self["mark_in"]
        if new_val:
            self["mark_out"] = new_val
        return self["mark_out"]

    @property
    def file_path(self):
        try:
            return os.path.join(storages[self["id_storage"]].local_path, self["path"])
        except:
            return "/dev/null/non_existent_file"

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
    _asset = False

    def new(self):
        super(BaseItem, self).new()
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
    def new(self):
        super(BaseBin, self).new()
        self.items = []


class BaseEvent(BaseObject):
    def new(self):
        super(BaseBin, self).new()
        self["start"]      = 0
        self["stop"]       = 0
        self["id_channel"] = 0
        self["id_magic"]   = 0

class BaseUser(BaseObject):
    pass
