from .core import *
from .db import *

__all__ = ["Asset"]


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
        self.meta = kwargs.get("meta", {})
        self._db = kwargs.get("db", False)

    @property
    def id(self):
        return self.meta.get("id", False)

    def __getitem__(self, key):
        return self.meta[key]

    def __setitem__(self, key, value):
        self.meta[key] = value

    @property
    def ft_index(self):
        return create_ft_index(self.meta)

    @property
    def db(self):
        if not self._db:
            self._db = DB()
        return self._db

    def save(self):
        if self.id:
            self._update()
        else:
            self._insert()

    def _insert(self):
        db_map = self.db_map
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
                "metadata" : json.dumps(self.meta),
                "ft_index" : self.ft_index
            }

