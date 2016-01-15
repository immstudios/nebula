from nx import *
from nx.objects import *

BLOCK_MODES = ["LINK", "MANUAL", "SOFT AUTO", "HARD AUTO"]

##################################################################################
## MACRO SCHEDULING BEGIN

def api_get_events(user, **kwargs):
    start_time = kwargs.get("start_time", 0)
    end_time = kwargs.get("end_time", start_time + (3600*24*7))
    extend = kwargs.get("extend", False)
    id_channel = kwargs.get("id_channel", False)

    if not id_channel:
        return 400, "No such playout channel"

    logging.debug("Requested events from {} to {}".format(
        time.strftime("%Y-%m-%d", time.localtime(start_time)),
        time.strftime("%Y-%m-%d", time.localtime(end_time)),
        ))

    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start >= %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
    res = db.fetchall()

    if extend:
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start < %s ORDER BY start DESC LIMIT 1", (id_channel, start_time))
        res = db.fetchall() + res

    logging.debug("Returning {} events".format(len(res)))

    result = []
    for id_event, in res:
        event = Event(id_event, db=db)
        event["duration"] = event.bin.duration
        result.append(event.meta)
    return 200, result


ASSET_TO_EVENT_INHERIT = [
    "title",
    "title/subtitle",
    "title/alternate",
    "title/series",
    "title/original",
    "description",
    "promoted"
    ]


def api_set_events(user, **kwargs):
    delete = kwargs.get("delete", [])
    events = kwargs.get("events", [])
    id_channel = kwargs.get("id_channel", 0)

    db = DB()

    changed_ids = []

    if id_channel and not user.has_right("scheduler_edit"):
        return 403, "Set events: access denied"

    logging.info("{} executes set_event method".format(user))

    deleted = created = updated = 0
    for id_event in kwargs.get("delete", []):
        event = Event(id_event, db=db)

        if not user.has_right("scheduler_edit", event["id_channel"]):
            return 403, "Delete events: access denied"

        if not event:
            logging.warning("Unable to delete non existent event ID {}".format(id_event))
            continue

        event.bin.delete()
        event.delete()
        deleted += 1
        changed_ids.append(event.id)


    for event_data in kwargs.get("events", []):
        id_event = event_data.get("id_object", False)
        id_channel = id_channel or event_data.get("id_channel", False)

        if not user.has_right("scheduler_edit", id_channel):
            return 403, "Delete events: access denied"

        pbin = False
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start = %s", [event_data.get("id_channel", id_channel), event_data["start"]])
        try:
            event_at_pos = db.fetchall()[0][0]
        except:
            event_at_pos = False

        if id_event:
            event = Event(id_event, db=db)
            if not event:
                logging.warning("No such event id {}".format(id_event))
                continue
            updated +=1
        elif event_at_pos:
            event = Event(event_at_pos, db=db)
            updated += 1
        elif id_channel:
            event = Event(db=db)
            pbin = Bin(db=db)
            pbin.save()
            event["id_magic"] = pbin.id
            event["id_channel"] = id_channel
            created +=1
        else:
            logging.warning("err... no : {}".format(kwargs))
            continue

        id_asset = event_data.get("id_asset", False)
        if id_asset and id_asset != event["id_asset"]:
            asset = Asset(id_asset, db=db)
            if asset:
                logging.info("Replacing event primary asset")
                pbin = pbin or event.bin

                pbin.delete_childs()
                pbin.items = []

                item = Item(db=db)
                item["id_asset"] = asset.id
                item["position"] = 1
                item["id_bin"] = pbin.id
                item.save()
                pbin.items.append(item)
                pbin.save()

                event["id_asset"] = asset.id
                for key in ASSET_TO_EVENT_INHERIT:
                    if asset[key]:
                        event[key] = asset[key]

        for key in event_data:
            if key == "id_magic" and not event_data[key]:
                continue
            event.meta[key] = event_data[key]

        changed_ids.append(event.id)
        event.save()

    messaging.send("objects_changed", objects=changed_ids, object_type="event", user=user.__repr__())

    return 200, "TODO: Statistics"



def api_get_runs(user, **kwargs):
    asset_ids  = kwargs.get("asset_ids", [])
    id_channel = int(kwargs.get("id_channel", 0))

    if not asset_ids:
        return 400, "Bad request"

    conds = "" # TOOD : start and stop time
    id_asset_cond = ", ".join([str(id_asset) for id_asset in asset_ids if type(id_asset) == int])

    db = DB()
    db.query("""SELECT DISTINCT(e.id_object) FROM nx_items as i, nx_events as e
        WHERE e.id_channel = {}
        AND i.id_asset IN ({})
        AND e.id_magic = i.id_bin
        {}
        """.format(id_channel, id_asset_cond, conds))

    #TODO: Take past items from nx_asrun instead of "scheduled" times

    result = []
    for id_event, in db.fetchall():
        event = Event(id_event, db=db)
        start = event["start"]
        for item in event.bin.items:
            if item["id_asset"] in asset_ids:
                result.append([id_event, item["id_asset"], start, False])
            start += item._duration


    return 200, {"data": result}





## MACRO SCHEDULING END
##################################################################################
## MICRO SCHEDULING BEGIN



def api_rundown(user, **kwargs):
    start_time = kwargs.get("start_time", 0)
    try:
        id_channel = int(kwargs["id_channel"])
        channel_config = config["playout_channels"][id_channel]
    except:
        return 400, "No such playout channel"

    db = DB()

    job_progress = {}
    if channel_config.get("send_action"):
        db.query("SELECT id_object, progress FROM nx_jobs WHERE id_action = %s AND progress >= -1", [channel_config["send_action"]])
        job_progress = {id_object: progress for id_object, progress in db.fetchall()}

    end_time   = start_time + (3600*24)
    item_runs  = get_item_runs(id_channel, start_time, end_time, db=db)
    data = []

    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start >= %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))

    ts_broadcast = 0
    events = db.fetchall()
    rlen = float(len(events))
    for i, e in enumerate(events):
        id_event = e[0]
        event = Event(id_event, db=db)

        if event["run_mode"]:
            ts_broadcast = 0

        event_meta = event.meta
        event_meta["rundown_scheduled"] = ts_scheduled = event["start"]
        event_meta["rundown_broadcast"] = ts_broadcast = ts_broadcast or ts_scheduled

        bin_meta   = event.bin.meta
        items = []
        for item in event.bin.items:
            i_meta = item.meta
            if item["id_asset"]:
                a_meta = item.asset.meta
            else:
                a_meta = {}

            as_start, as_stop = item_runs.get(item.id, (0, 0))
            if as_start:
                ts_broadcast = as_start

            i_meta["asset_mtime"] = a_meta.get("mtime", 0)
            i_meta["rundown_scheduled"] = ts_scheduled
            i_meta["rundown_broadcast"] = ts_broadcast

            ts_scheduled += item.duration
            ts_broadcast += item.duration

            # ITEM STATUS
            #
            # -1 : AIRED
            # -2 : Partialy aired. Probably still on air or play service was restarted during broadcast
            #  0 : Master asset is offline. Show as "OFFLINE"
            #  1 : Master asset is online, but playout asset does not exist or is offline
            #  2 : Playout asset is online. Show as "READY"

            if as_start and as_stop:
                i_meta["rundown_status"] = -1 # AIRED
            elif as_start:
                i_meta["rundown_status"] = -2 #  PART AIRED
            elif not item["id_asset"]:
                i_meta["rundown_status"] = 2 # Virtual item or something... show as ready
            elif item.asset["status"] != ONLINE:
                i_meta["rundown_status"] = 0 # Master asset is not online: Rundown status = OFFLINE
            else:
                id_playout = item[config["playout_channels"][id_channel]["playout_spec"]]
                if not id_playout or Asset(id_playout, db=db)["status"] not in [ONLINE, CREATING]: # Master asset exists, but playout asset is not online.... (not scheduled / pending)
                    i_meta["rundown_status"] = 1
                else:
                    i_meta["rundown_status"] = 2 # Playout asset is ready

            if item["id_asset"] in job_progress:
                item["rundown_transfer_progress"] = job_progress[item["id_asset"]]

            items.append(i_meta)

        # Reset broadcast time indicator after empty blocks and if run mode is not AUTO (0)
        if not event.bin.items:
            ts_broadcast = 0

        data.append({
                "event_meta" : event_meta,
                "bin_meta"   : bin_meta,
                "items"      : items
            })

    return 200, data



def api_bin_order(user, **kwargs):
    id_channel = kwargs.get("id_channel", False) # Optional. Just for playlist-bin.

    if not user or (id_channel and not user.has_right("rundown_edit", id_channel)):
        return 403, "Not authorised"

    id_bin = kwargs.get("id_bin", False)
    order  = kwargs.get("order", [])
    sender = kwargs.get("sender", False)

    append_cond = "True"
    if id_channel:
        append_cond = config["playout_channels"][id_channel].get("rundown_accepts", "True")

        if not user.has_right("rundown_edit", event["id_channel"]):
            return 403, "bin_order: access denied"

    if not (id_bin and order):
        return 400, "Bad request"

    affected_bins = [id_bin]
    pos = 1

    logging.info("{} executes bin_order method".format(user))

    db = DB()
    rlen = float(len(order))
    for i, obj in enumerate(order):
        object_type = obj["object_type"]
        id_object   = obj["id_object"]
        kwargs      = obj["kwargs"]

        if object_type == ITEM:
            if not id_object:
                item = Item(db=db)
                item["id_asset"] = obj.get("id_asset", 0)
                item.meta.update(kwargs)
            else:
                item = Item(id_object, db=db)

                if not item:
                    logging.debug("Skipping {}".format(item))
                    continue

            if not item["id_bin"] in affected_bins:
                affected_bins.append(item["id_bin"])

        elif object_type == ASSET:
            asset = Asset(id_object, db=db)
            try:
                can_append = eval(append_cond)
            except:
                logging.error("Unable to evaluate rundown accept condition: {}".format(append_cond))
                continue
            if not asset or not can_append:
                continue

            item = Item(db=db)
            item["id_asset"] = asset.id
            item.meta.update(kwargs)

        else:
            continue

        if not item or item["position"] != pos or item["id_bin"] != id_bin:
            item["position"] = pos
            item["id_bin"]   = id_bin
            item.save()
        pos += 1

    bin_refresh(affected_bins, sender, db)
    return 200, "OK"



def api_del_items(user, **kwargs):
    items = kwargs.get("items",[])
    sender = kwargs.get("sender", False)
    affected_bins = []
    logging.info("{} executes del_items method".format(user))
    db = DB()
    for id_item in items:
        item = Item(id_item, db=db)
        if not item["id_bin"] in affected_bins and item["id_bin"]:
                affected_bins.append(item["id_bin"])
        item.delete()
    bin_refresh(affected_bins, sender, db)
    return 202, "OK"
