#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    import yaml
except:
    yaml = False

from nx.common import *
from nx.common.metadata import meta_types
from nx.connection import *

from nx.common.base_objects import BaseObject,  BaseAsset, BaseItem, BaseBin, BaseEvent


class ServerObject(object):
    @property 
    def db(self):
        if not self._db:
            logging.info("{} is opening DB connection".format(self))
            self._db = DB()
        return self._db

    @property 
    def cache(self):
        return self._cache or cache

    def _load(self):
        if not self._load_from_cache():
            logging.debug("Loading {!r} from DB".format(self))

            qcols = ", ".join(self.ns_tags)
            self.db.query("SELECT {0} FROM nx_{1}s WHERE id_object={2}".format(qcols, self.object_type, self.id))
            try:
                result = self.db.fetchall()[0]
            except:
                logging.error("Unable to load {!r}".format(self))
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            self.db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (self["id_object"], self.id_object_type()))
            for tag, value in self.db.fetchall():
                self[tag] = value

            self._save_to_cache()
        return True

    def _load_from_cache(self):
        try:
            self.meta = json.loads(self.cache.load("{0}{1}".format(self.ns_prefix, self.id)))
        except:
            return False
        else:
            if self.meta:
                return True
            return False

    def _save_to_cache(self):
        return self.cache.save("{0}{1}".format(self.ns_prefix, self["id_object"]), json.dumps(self.meta))

    def _save(self,**kwargs):
        created = False
        if self["id_object"]:
            q = "UPDATE nx_{0}s SET {1} WHERE id_object = {2}".format(self.object_type,
                                                                  ", ".join("{} = %s".format(tag) for tag in self.ns_tags if tag != "id_object"),
                                                                  self["id_object"]
                                                                  )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            self.db.query(q, v)
            self.db.query("DELETE FROM nx_meta WHERE id_object = {0} and object_type = {1}".format(self["id_object"], self.id_object_type()))
        else:
            self["ctime"] = self["ctime"] or time.time()
            created = True
            q = "INSERT INTO nx_{0}s ({1}) VALUES ({2})".format( self.object_type,  
                                                          ", ".join(tag for tag in self.ns_tags if tag != 'id_object'),
                                                          ", ".join(["%s"]*(len(self.ns_tags)-1)) 
                                                        )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            self.db.query(q, v)
            self["id_object"] = self.id = self.db.lastid()
            logging.info("{!r} created".format(self))

        for tag in self.meta:
            if tag in self.ns_tags:
                continue
            value = meta_types.unformat(tag, self.meta[tag])
            q = "INSERT INTO nx_meta (id_object, object_type, tag, value) VALUES (%s, %s, %s, %s)"
            v = [self["id_object"], self.id_object_type(), tag, value]
            self.db.query(q, v)

        if self._save_to_cache():
            self.db.commit()
            if kwargs.get("notify", True) and not created:
                messaging.send("objects_changed", objects=[self.id], object_type=self.object_type, user=config["user"])
            return True
        else:
            logging.error("Save {!r} to cache failed".format(self))
            self.db.rollback()
            return False

    def delete_childs(self):
        return True

    def delete(self):
        logging.debug("Deleting {!r}".format(self))
        if self.delete_childs():
            self.db.query("DELETE FROM nx_meta WHERE id_object = %s and object_type = %s", [self.id, self.id_object_type()] )
            self.db.query("DELETE FROM nx_{}s WHERE id_object = %s".format(self.object_type), [self.id])
            self.db.commit()
            self.cache.delete("{0}{1}".format(self.ns_prefix, self.id))
            logging.info("{!r} deleted.".format(self))
            return True
        return False








class Asset(ServerObject, BaseAsset):
    object_type = "asset"

    def load_sidecar_metadata(self):
        path_elms = os.path.splitext(self.file_path)[0].split("/")[1:]
        for i in range(len(path_elms)):

            nxmeta_name = "/" + reduce(os.path.join, path_elms[:i]+["{}.json".format(path_elms[i])])
            if os.path.exists(nxmeta_name):
                try:
                    self.meta.update(json.loads(open(nxmeta_name).read()))
                except:
                    logging.warning("Unable to parse %s" % nxmeta_name)
                else:
                    logging.debug("Applied meta from template %s" % nxmeta_name)

            nxmeta_name = "/" + reduce(os.path.join, path_elms[:i]+["{}.yaml".format(path_elms[i])])
            if os.path.exists(nxmeta_name):
                if not yaml:
                    logging.warning("YAML sidecar file exists, but pyyaml is not installed")
                    continue
                try:
                    f = open(nxmeta_name)
                    m = yaml.safe_load(f)
                    f.close()
                    self.meta.update(m)
                except:
                    logging.warning("Unable to parse %s" % nxmeta_name)
                else:
                    logging.debug("Applied meta from template {}".format(nxmeta_name))




class Item(ServerObject, BaseItem): 
    @property
    def asset(self):
        if not self._asset:
            if self.meta.get("id_asset", 0):
                self._asset = Asset(self["id_asset"], db=self._db, cache=self._cache)
            else:
                return False
        return self._asset

    @property
    def bin(self):
        if not hasattr(self, "_bin"):
            self._bin = Bin(self["id_bin"], db=self._db, cache=self._cache)
        return self._bin

    @property
    def event(self):
        id_bin = int(self["id_bin"])
        if not id_bin:
            return False
        db = self._db
        if not hasattr(self, "_event"):
            db.query("SELECT id_object FROM nx_events WHERE id_magic=%s", [id_bin])
            res = db.fetchall()
            if not res:
                self._event = False
            else:
                self._event = Event(res[0][0], db=self._db, cache=self._cache)
        return self._event




class Bin(ServerObject, BaseBin):
    object_type = "bin"
    def _load(self):
        if not self._load_from_cache():
            logging.debug("Loading {!r} from DB".format(self))

            qcols = ", ".join(self.ns_tags)
            self.db.query("SELECT {0} FROM nx_{1}s WHERE id_object={2}".format(qcols, self.object_type, self.id))
            try:
                result = self.db.fetchall()[0]
            except:
                logging.error("Unable to load {!r}".format(self))
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            self.db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (self["id_object"], self.id_object_type()))
            for tag, value in self.db.fetchall():
                self[tag] = value

            self.db.query("SELECT id_object FROM nx_items WHERE id_bin = %s ORDER BY position", [self["id_object"]])
            self.items = []
            for id_item, in self.db.fetchall():
                self.items.append(Item(id_item, db=self._db))
            self._save_to_cache()
        return True


    def _load_from_cache(self):
        try:
            self.meta, itemdata = json.loads(self.cache.load("%s%d" % (self.ns_prefix, self.id)))
        except:
            return False
        self.items = []
        for idata in itemdata:
            self.items.append(Item(from_data=idata, db=self._db))
        return True

    def _save_to_cache(self):
        return self.cache.save("%s%d" % (self.ns_prefix, self["id_object"]), json.dumps([self.meta, [i.meta for i in self.items]]))

    @property
    def duration(self):
        dur = 0
        for item in self.items:
            dur += item.get_duration()
        return dur

    def delete_childs(self):
        for item in self.items:
            if item.id > 0:
                item.delete()
        return True


class Event(ServerObject, BaseEvent):
    @property
    def bin(self):
        if not self._bin:
            self._bin = Bin(self["id_magic"], db=self._db, cache=self.cache)
        return self._bin

    @property
    def asset(self):
        if not self._asset:
            self._asset = Asset(self["id_magic"], db=self._db, cache=self.cache)
        return self._asset


class User(ServerObject, BaseObject):
    object_type = "user"

    def set_password(self, password):
        self["password"] = get_hash(password)

    def has_right(self, key, val=True):
        if self["is_admin"]:
            return True
        key = "can/{}".format(key)
        if not self[key]:
            return False
        return self[key] == True or (type(self[key]) == list and val in self[key])

    def __getitem__(self, key):
        if self.meta.get("is_admin", False) and key.startswith("can/"):
            return True
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]

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
        except:
            return iid

######################################################################################
## Utilities


def get_user(login, password, db=False):
    #TODO: sanitize inputs
    if not db: 
        db = DB()
    db.query("SELECT id_object FROM nx_users WHERE login=%s and password=%s", [login, get_hash(password)])
    res = db.fetchall()
    if not res:
        return False
    return User(res[0][0])



def asset_by_path(id_storage, path, db=False):
    if not db:
        db = DB()
    db.query("""SELECT id_object FROM nx_meta 
                WHERE object_type = 0 
                AND tag='id_storage' 
                AND value='%s' 
                AND id_object IN (SELECT id_object FROM nx_meta WHERE object_type = 0 AND tag='path' AND value='%s')
                """ % (id_storage, db.sanit(path.replace("\\","/"))))
    try:
        return db.fetchall()[0][0]
    except:
        return False


def asset_by_full_path(path, db=False):
    if not db:
        db = DB()
    for s in storages:
        if path.startswith(storages[s].get_path()):
            return asset_by_path(s,path.lstrip(s.path),db=db)
    return False


def meta_exists(tag, value, db=False):
    if not db: 
        db = DB()
    db.query("""SELECT a.id_asset FROM nx_meta as m, nx_assets as a 
                WHERE a.status <> 'TRASHED' 
                AND a.id_asset = m.id_object
                AND m.object_type = 0
                AND m.tag='%s' 
                AND m.value='%s'
                """ % (tag, value))
    try:
        return res[0][0]
    except:
        return False





def bin_refresh(bins, sender=False, db=False):
    if not bins:
        return 200, "No bin refreshed"
    if not db:
        db = DB()
    for id_bin in bins:
        cache.delete("b{}".format(id_bin))
    bq = ", ".join([str(b) for b in bins if b])
    changed_events = []
    db.query("SELECT e.id_object, e.id_channel, e.start FROM nx_events as e, nx_channels as c WHERE c.channel_type = 0 AND c.id_channel = e.id_channel AND id_magic in ({})".format(bq))
    for id_event, id_channel, start_time in db.fetchall():
        chg = id_event
        if not chg in changed_events:
            changed_events.append(chg)
    if changed_events:
        messaging.send("objects_changed", sender=sender, objects=changed_events, object_type="event")
    return 202, "OK"


def get_day_events(id_channel, date, num_days=1):
    start_time = datestr2ts(date, *config["playout_channels"][id_channel].get("day_start", [6,0]))
    end_time   = start_time + (3600*24*num_days)
    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel=%s AND start > %s AND start < %s ", (id_channel, start_time, end_time))
    for id_event, in db.fetchall():
        yield Event(id_event)


def get_bin_first_item(id_bin, db=False):
    if not db:
        db = DB()
    db.query("SELECT id_item FROM nx_items WHERE id_bin=%d ORDER BY position LIMIT 1" % id_bin)
    try:
        return db.fetchall()[0][0]
    except:
        return False


def get_item_event(id_item, **kwargs):
    db = kwargs.get("db", DB())
    lcache = kwargs.get("cahce", cache)

    db.query("""SELECT e.id_object, e.start, e.id_channel from nx_items as i, nx_events as e where e.id_magic = i.id_bin and i.id_object = {} and e.id_channel in ({})""".format(
        id_item,
        ", ".join([str(f) for f in config["playout_channels"].keys()]) 
        ))
    try:
        id_object, start, id_channel = db.fetchall()[0]
    except:
        return False
    return Event(id_object, db=db, cache=lcache)


def get_item_runs(id_channel, from_ts, to_ts, db=False):
    db = db or DB()
    db.query("SELECT id_item, start, stop FROM nx_asrun WHERE start >= %s and start < %s ORDER BY start ASC", [int(from_ts), int(to_ts)] )
    result = {}
    for id_item, start, stop in db.fetchall():
        result[id_item] = (start, stop)
    return result


def get_next_item(id_item, **kwargs):
    if not id_item:
        return False
    db = kwargs.get("db", DB())
    lcache = kwargs.get("cache", cache)

    logging.debug("Looking for item following item ID {}".format(id_item))
    current_item = Item(id_item, db=db, cache=lcache)
    current_bin = Bin(current_item["id_bin"], db=db, cache=lcache)
    for item in current_bin.items:
        if item["position"] > current_item["position"]:
            if item["item_role"] == "lead_out":
                logging.info("Cueing Lead In")
                for i, r in enumerate(current_bin.items):
                    if r["item_role"] == "lead_in":
                        return r
                else:
                    return current_bin.items[0]
            return item
    else:
        current_event = get_item_event(id_item, db=db, cache=lcache)
        q = "SELECT id_object FROM nx_events WHERE id_channel = {} and start > {} ORDER BY start ASC LIMIT 1".format(current_event["id_channel"], current_event["start"])
        db.query(q)
        try:
            next_event = Event(db.fetchall()[0][0], db=db, cache=lcache)
            if not next_event.bin.items:
                raise Exception
            if next_event["run_mode"]:
                raise Exception
            return next_event.bin.items[0]
        except:
            logging.info("Looping current playlist")
            return current_bin.items[0]
