from .core import *
from .core.base_objects import *
from .db import *

__all__ = ["Asset", "Item", "Bin", "Event", "User"]

def create_ft_index(meta):
    idx = set()
    for key in meta:
        if not key in meta_types:
            continue
        if not meta_types[key].searchable:
            continue
        slug_set = slugify(meta[key], make_set=True, min_length=3)
        idx |= slug_set
    return " ".join(idx)


class NebulaObject(object):
    @property
    def db(self):
        if not self._db:
            logging.debug("{} is opening DB connection.".format(self.__repr__().capitalize()))
            self._db = DB()
        return self._db

    def save(self, **kwargs):
        if kwargs.get("set_mtime", True):
            self["mtime"] = int(time.time())
        if self.is_new:
            self._insert()
        else:
            self._update()
        self.db.commit()

    def _insert(self):
        db_map = self.db_map
        db_map["meta"] = json.dumps(self.meta)
        if self.id:
            db_map["id"] = self.id # For object migration
        columns = []
        values = []
        for key in db_map:
            columns.append(key)
            values.append(db_map[key])
        val_placeholder = ", ".join(["%s"]*len(db_map))
        columns = ", ".join(columns)
        query = "INSERT INTO {} ({}) VALUES ({})".format(self.db_table, columns, val_placeholder)
        self.db.query(query, values)
        if not self.id: # this is not very effective, but we need to have id in meta json
            self["id"] = self.db.lastid()
            self.db.query("UPDATE {} SET meta=%s WHERE id=%s".format(self.db_table), [json.dumps(self.meta), self.id])

    def _update(self):
        db_map = self.db_map
        db_map["meta"] = json.dumps(self.meta)
        elms = []
        for key in db_map:
            elms.append("{}=%s".format(key))
            values.append(db_map[key])
        elms = ", ".join(elms)
        values.append(self.id)
        query = "UPDATE {} SET {} WHERE id=%s".format(self.db_table, elms)






class Asset(NebulaObject, BaseAsset):
    @property
    def ft_index(self):
        return create_ft_index(self.meta)

    @property
    def db_table(self):
        return "assets"

    @property
    def db_map(self):
        return {
                "content_type" : self["content_type"],
                "media_type" : self["media_type"],
                "id_folder" : self["id_folder"],
                "origin" : self["origin"],
                "status" : self["status"],
                "ft_index" : self.ft_index
            }


class Item(NebulaObject, BaseItem):
    @property
    def db_table(self):
        return "items"

    @property
    def db_map(self):
        return {
            }

class Bin(NebulaObject, BaseBin):
    @property
    def db_table(self):
        return "bins"

    @property
    def db_map(self):
        return {
            }


class Event(NebulaObject, BaseEvent):
    @property
    def db_table(self):
        return "events"

    @property
    def db_map(self):
        return {
                "event_type" : self["event_type"],
                "start_time" : self["start_time"],
                "end_time" : self["end_time"],
                "id_magic" : self["id_magic"],
            }

class User(NebulaObject, BaseUser):
    @property
    def db_table(self):
        return "users"

    @property
    def db_map(self):
        return {
                "login" : self["login"],
                "password" : self["password"],
            }

    def set_password(self, password):
        self["password"] = get_hash(password)

