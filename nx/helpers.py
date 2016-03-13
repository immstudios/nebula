from .core import *
from .db import *
from .objects import *

__all__ = [
        "get_user",
        "asset_by_path",
        "asset_by_full_path",
    ]

def get_user(login, password, db=False):
    if not db:
        db = DB()
    db.query("SELECT metadata FROM users WHERE login=%s and password=%s", [login, get_hash(password)])
    res = db.fetchall()
    if not res:
        return False
    return User(meta=res[0][0])


def asset_by_path(id_storage, path, db=False):
    path = path.replace("\\", "/")
    if not db:
        db = DB()
    db.query("""
            SELECT id FROM assets
                WHERE metadata->>'id_storage' = %s
                AND metadata->>'path' = %s
        """, [id_storage, path])
    try:
        return db.fetchall()[0][0]
    except:
        return False


def asset_by_full_path(path, db=False):
    if not db:
        db = DB()
    for s in storages:
        if path.startswith(storages[s].local_path):
            return asset_by_path(s,path.lstrip(s.path),db=db)
    return False


##
## TO BE UPDATED
##


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
