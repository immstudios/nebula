from nebulacore import *
from .connection import *
from .objects import *


def get_user(login, password, db=False):
    if not db:
        db = DB()
    db.query("SELECT meta FROM users WHERE login=%s AND password=%s", [login, get_hash(password)])
    res = db.fetchall()
    if not res:
        return False
    return User(meta=res[0][0])


def asset_by_path(id_storage, path, db=False):
    path = path.replace("\\", "/")
    if not db:
        db = DB()
    db.query("""
            SELECT id, meta FROM assets
                WHERE meta->>'id_storage' = %s
                AND meta->>'path' = %s
        """, [id_storage, path])
    res = db.fetchall()
    for id, meta in db.fetchall():
        return Asset(meta=meta, db=db)
    return False


def asset_by_full_path(path, db=False):
    if not db:
        db = DB()
    for id_storage in storages:
        if path.startswith(storages[id_storage].local_path):
            return asset_by_path(id_storage, path.lstrip(storages[id_storage]["path"]), db=db)
    return False


def meta_exists(key, value, db=False):
    if not db:
        db = DB()
    db.query("SELECT id, meta FROM assets WHERE meta->>'%s' = '%s'", [key, value])
    for id, meta in db.fetchall():
        return Asset(meta=meta, db=db)
    return False


def bin_refresh(bins, sender=False, db=False):
    if not bins:
        return 200, "No bin refreshed"
    if not db:
        db = DB()
    for id_bin in bins:
        cache.delete("b{}".format(id_bin))
    bq = ", ".join([str(b) for b in bins if type(b) == int or b.isdigit()])
    changed_events = []
    db.query("""
        SELECT e.id, e.id_channel, e.start FROM events AS e, channels AS c
            WHERE c.channel_type = 0
            AND c.id_channel = e.id_channel
            AND id_magic in ({})
            """.format(bq))
    for id_event, id_channel, start_time in db.fetchall():
        chg = id_event
        if not chg in changed_events:
            changed_events.append(chg)
    if changed_events:
        messaging.send("objects_changed", sender=sender, objects=changed_events, object_type="event")
    return 202, "OK"


def get_day_events(id_channel, date, num_days=1):
    start_time = datestr2ts(date, *config["playout_channels"][id_channel].get("day_start", [6,0]))
    end_time = start_time + (3600*24*num_days)
    db = DB()
    db.query("SELECT id, meta FROM events WHERE id_channel=%s AND start > %s AND start < %s ", (id_channel, start_time, end_time))
    for id_event, meta in db.fetchall():
        yield Event(meta=meta)


def get_bin_first_item(id_bin, db=False):
    if not db:
        db = DB()
    db.query("SELECT id, meta FROM items WHERE id_bin=%s ORDER BY position LIMIT 1", [id_bin])
    for id, meta in db.fetchall():
        return Item(meta=meta, db=db)
    return False


def get_item_event(id_item, **kwargs):
    db = kwargs.get("db", DB())
    lcache = kwargs.get("cahce", cache)
    #TODO: Use db mogrify
    db.query("""SELECT e.id_object, e.meta FROM items AS i, events AS e WHERE e.id_magic = i.id_bin AND i.id = {} and e.id_channel in ({})""".format(
        id_item,
        ", ".join([str(f) for f in config["playout_channels"].keys()])
        ))
    for id, meta in db.fetchall():
        return Event(meta=meta, db=db)
    return False


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
