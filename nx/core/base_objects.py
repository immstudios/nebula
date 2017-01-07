import pprint

from .common import *
from .constants import *
from .metadata import meta_types

__all__ = ["BaseObject", "AssetMixIn", "ItemMixIn", "BinMixIn", "EventMixIn", "UserMixIn"]

class BaseObject(object):
    defaults = {}

    def __init__(self, id=False, **kwargs):
        self.text_changed = self.meta_changed = False
        self.is_new = True
        self.meta = {}
        meta = kwargs.get("meta", {})
        assert meta is not None, "Unable to load {}.  Meta must not be 'None'.".format(self.object_type)
        assert hasattr(meta, "keys"), "Incorrect meta!"
        for key in meta:
            self.meta[key] = meta[key]
        if "id" in self.meta:
            self.is_new = False
        elif not self.meta:
            if id:
                self.load(id)
                self.is_new = False
            else:
                self.new()
                self.is_new = True
        for key in self.defaults:
            if not key in self.meta:
                self.meta[key] = self.defaults[key]

    @property
    def id(self):
        return self.meta.get("id", False)

    @property
    def object_type(self):
        return self.__class__.__name__.lower()

    def keys(self):
        return self.meta.keys()

    def __getitem__(self, key):
        key = key.lower().strip()
        if key == "_duration":
            return self.duration
        return self.meta.get(key, meta_types[key].default)

    def __setitem__(self, key, value):
        key = key.lower().strip()
        meta_type = meta_types[key]
        value = meta_type.validate(value)
        if value == self[key]:
            return True # No change
        self.meta_changed = True
        if meta_type["fulltext"]:
            self.text_changed = True
        if not value:
            del self[key]
        else:
            self.meta[key] = value
        return True

    def update(self, data):
        for key in data.keys():
            self[key] = data[key]

    def new(self):
        logging.debug("Creating empty {}".format(self.object_type))

    def load(self, id):
        pass

    def save(self, **kwargs):
        self["ctime"] = self["ctime"] or time.time()
        if kwargs.get("set_mtime", True):
            self["mtime"] = int(time.time())
        for key in self.required:
            assert key in self.meta, "Unable to save {}. {} is required".format(self, key)

    def delete(self, **kwargs):
        assert self.id > 0, "Unable to delete unsaved object"

    def __delitem__(self, key):
        key = key.lower().strip()
        if not key in self.meta:
            return
        if hasattr(self, "ns_tags") and key in self.ns_tags:
            return #v4 only
        del self.meta[key]

    def __repr__(self):
        if self.id:
            result = "{} ID:{}".format(self.object_type, self.id)
        else:
            result = "new {}".format(self.object_type)
        title = self.meta.get("title", "").encode("utf8", "replace")
        if title:
            result += " ({})".format(title)
        return result

    def __len__(self):
        return not self.is_new

    def show(self, key, **kwargs):
        return meta_types[key.lstrip("_")].show(self[key], **kwargs)

    def show_meta(self):
        return pprint.pformat(self.meta)






class AssetMixIn():
    object_type_id = 0
    required = ["media_type", "content_type", "id_folder", "ctime", "mtime"]
    defaults = {"media_type" : VIRTUAL, "content_type" : TEXT}

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
        if self["media_type"] != FILE:
            return ""
        try:
            return os.path.join(storages[int(self["id_storage"])].local_path, self["path"])
        except (KeyError, IndexError, ValueError):
            # Yes. empty string. keep it this way!!! (because of os.path.exists and so on)
            # Also: it evals as false
            return ""

    @property
    def duration(self):
        dur = float(self.meta.get("duration",0))
        mki = float(self.meta.get("mark_in" ,0))
        mko = float(self.meta.get("mark_out",0))
        if not dur:
            return 0
        if mko > 0:
            dur -= dur - mko
        if mki > 0:
            dur -= mki
        return dur

    @property
    def proxy_url(self):
        base_url = config["proxy_base_url"]
        return  base_url + "/{:04d}/{:d}.mp4".format(int(self.id/1000),  self.id)


class ItemMixIn():
    object_type_id = 1
    required = ["id_bin", "id_asset", "position", "ctime", "mtime"]

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


class BinMixIn():
    object_type_id = 2
    required = ["bin_type", "ctime", "mtime"]
    defaults = {"bin_type" : 0}

    @property
    def duration(self):
        dur = 0
        for item in self.items:
            dur += item.duration
        return dur


class EventMixIn():
    object_type_id = 3
    required = ["start", "id_channel", "ctime", "mtime"]


class UserMixIn():
    object_type_id = 4
    required = ["login", "password"]

    def set_password(self, password):
        self["password"] = get_hash(password)

    def __repr__(self):
        if self.id:
            iid = "{} ID:{}".format(self.object_type, self.id)
        else:
            iid = "new {}".format(self.object_type)
        try:
            title = self["login"] or ""
            if title:
                title = " ({})".format(title)
            return "{}{}".format(iid, title)
        except Exception:
            return iid
