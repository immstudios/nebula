from nx import *

__all__ = ["get_rundown", "api_rundown"]


def get_rundown(id_channel, start_time):
    db = DB()
    end_time = start_time + (3600 * 24)

    #FIXME    item_runs  = get_item_runs(id_channel, start_time, end_time, db=db)
    item_runs = {}

    db.query("""
            SELECT
                e.id,
                e.meta,
                i.meta,
                a.meta
            FROM
                events AS e,
                items AS i
            LEFT JOIN
                assets AS a
            ON
                i.id_asset = a.id
            WHERE
                e.id_channel = %s AND e.start >= %s AND e.start < %s
            AND
                e.id_magic = i.id_bin
            ORDER BY
                e.start ASC,
                i.position ASC
            """, (id_channel, start_time, end_time))

    current_event_id = None
    event = None

    ts_broadcast = ts_scheduled = 0

    for id_event, emeta, imeta, ameta in db.fetchall() + [(-1, None, None, None)]:
        if id_event != current_event_id:
            if event:
                yield event
                if not event.items:
                    ts_broadcast = 0
            if id_event == -1:
                break

            event = Event(meta=emeta)
            event.items = []
            current_event_id = id_event

            if event["run_mode"]:
                ts_broadcast = 0
            event.meta["rundown_scheduled"] = ts_scheduled = event["start"]
            event.meta["rundown_broadcast"] = ts_broadcast = ts_broadcast or ts_scheduled


        asset = Asset(meta=ameta, db=db)
        item = Item(meta=imeta, db=db)
        item._asset = asset

        as_start, as_stop = item_runs.get(item.id, (0, 0))
        if as_start:
            ts_broadcast = as_start

        item.meta["asset_mtime"] = asset["mtime"]
        item.meta["rundown_scheduled"] = ts_scheduled
        item.meta["rundown_broadcast"] = ts_broadcast
        item.meta["rundown_difference"] = ts_broadcast - ts_scheduled

        ts_scheduled += item.duration
        ts_broadcast += item.duration

        event.items.append(item)








def api_rundown(**kwargs):
    id_channel = int(kwargs["id_channel"])
    start_time = kwargs.get("start_time", 0)

    process_start_time = time.time()
    if not id_channel:
        return {"response" : 400, message : "Request params error"}
    if not id_channel in config["playout_channels"]:
        return {"response" : 400, message : "No such playout channel"}

    if not start_time:
        # default today
        sh, sm = config["playout_channels"][id_channel].get("day_start", [6, 0])
        rundown_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        rundown_start_time = datestr2ts(rundown_date, hh=sh, mm=sm)
        rundown_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        start_time = datestr2ts(rundown_date, hh=sh, mm=sm)


    rows = []
    for event in get_rundown(id_channel, start_time):
        row = event.meta
        row["object_type"] = "event"
        rows.append(row)
        for item in event.items:
            row = item.meta
            row["object_type"] = "item"
            rows.append(row)

    process_time = time.time() - process_start_time
    return {"response" : 200, "message" : "Rundown loaded in {:.02f} seconds".format(process_time), "data" : rows}


