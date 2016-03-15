from .core import *
from .db import *

__all__ = ["Asset", "Item", "Bin", "Event", "User"]

def create_ft_index(meta):
    idx = set()
    for key in meta:
        if not key in meta_types:
            continue
        if not meta_types[key].ft:
            continue
        for elm in meta[key]:
            if len(elm) < 3:
                continue
            idx.add(unaccent(elm).lower())
    return " ".join(idx)


class NebulaObject(object):
    def __init__(self, id=False, **kwargs):
        super(NebulaObject).__init__(id, **kwargs)

    @property
    def db(self):
        if not self._db:
            logging.debug("{} is opening DB connection.".format(self.__repr__().capitalize()))
            self._db = DB()
        return self._db

    def save(self, **kwargs):
        if kwargs.get("set_mtime", True):
            self["mtime"] = int(time.time())
        if self.id:
            self._update()
        else:
            self._insert()

    def _insert(self):
        db_map = self.db_map
        db_map["metadata"] = self.meta
        columns = []
        values = []
        for key in db_map:
            columns.append(key)
            values.append(db_map[key])
        val_placeholder = ", ".join(["%s"]*len(db_map))
        columns = ", ".join(columns)
        query = "INSERT INTO {} ({}) VALUES ({})".format(self.db_table, columns, val_placeholder)
        self.db.query(query, values)
        self["id"] = self.db.lastid()
        self.db.commit()

    def _update(self):
        db_map = self.db_map
        db_map["metadata"] = self.meta
        elms = []
        for key in db_map:
            elms.append("{}=%s".format(key))
            values.append(db_map[key])
        elms = ", ".join(elms)
        values.append(self.id)
        query = "UPDATE {} SET {} WHERE id=%s".format(self.db_table, elms)
        self.db.query(query, values)






class Asset(NebulaObject):
    @property
    def db_table(self):
        return "assets"

    @property
    def db_map(self):
        return {
                "id_folder" : self["id_folder"],
                "id_origin" : self["id_origin"],
                "status" : self["status"],
                "ft_index" : create_ft_index(self.meta)
            }


class Item(NebulaObject):
    @property
    def db_table(self):
        return "items"

    @property
    def db_map(self):
        return {
            }

class Bin(NebulaObject):
    @property
    def db_table(self):
        return "bins"

    @property
    def db_map(self):
        return {
            }


class Event(NebulaObject):
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



class User(NebulaObject):
    @property
    def db_table(self):
        return "users"

    @property
    def db_map(self):
        return {
                "login" : self["login"],
                "password" : self["password"],
            }

