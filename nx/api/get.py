from nx import *

__all__ = ["api_get", "get_objects"]

def get_objects(ObjectType, **kwargs):
    """objects lookup function. To be used inside services"""

    db          = kwargs.get("db", DB())
    raw_conds   = kwargs.get("conds", [])
    fulltext    = kwargs.get("fulltext", False)
    result_type = kwargs.get("result", False)
    do_count    = kwargs.get("count", False)
    limit       = kwargs.get("limit", False)
    offset      = kwargs.get("offset", False)
    order       = kwargs.get("order", "ctime desc")
    id_view     = kwargs.get("id_view", False)
    objects     = kwargs.get("objects", [])


    try:
        order_key, order_trend = order.split(" ")
    except Exception:
        order_key = order
        order_trend = "ASC"

    if not order_trend.lower() in ["asc", "desc"]:
        order_trend = "ASC"
    order = "meta->>'{}' {}".format(order_key, order_trend)



    if objects:
        l = {"count": len(objects)}
        # We do not do database lookup. Just returning objects by their ids
        for id_object in objects:
            yield l, ObjectType(id_object, db=db)
        return


    view_count = False
    if id_view and id_view in config["views"]:
        view_config = config["views"][id_view]
        for key, col in [
                    ["folders", "id_folder"],
                    ["media_types", "media_type"],
                    ["content_types", "content_type"],
                    ["states", "status"],
                    ["folders", "id_folder"],
                ]:
            if key in view_config and view_config[key]:
                if len(view_config[key]) == 1:
                    raw_conds.append("{}={}".format(col, view_config[key][0]))
                else:
                    raw_conds.append("{} IN ({})".format(col, ",".join([str(v) for v in view_config[key]])))
        for cond in view_config.get("conds", []):
            raw_conds.append(cond)

    conds = []
    for cond in raw_conds:
        for col in ObjectType.db_cols:
            if cond.startswith(col):
                conds.append(cond)
                break
        else:
            conds.append("meta->>"+cond)

    if fulltext:
        do_count = True
        ft = slugify(fulltext, make_set=True)
        for word in ft:
            conds.append("id IN (SELECT id FROM ft WHERE object_type={} AND value LIKE '{}%')".format(ObjectType.object_type_id, word))
    else:
        if view_count:
            do_count = False
        else:
            do_count = True

    conds = " WHERE " + " AND ".join(conds) if conds else ""
    counter = ", count(id) OVER() AS full_count" if do_count else ", 0"

    q = "SELECT id, meta{} FROM {}{}".format(counter, ObjectType.table_name, conds)
    q += " ORDER BY {}".format(order) if order else ""
    q += " LIMIT {}".format(limit) if limit else ""
    q += " OFFSET {}".format(offset) if offset else ""

    logging.debug("Executing get query:", q)
    db.query(q)

    for id, meta, count in db.fetchall():
        yield {"count": count or view_count}, ObjectType(meta=meta, db=db)




def api_get(**kwargs):
    object_type = kwargs.get("object_type", "asset")
    objects = kwargs.get("objects") or kwargs.get("ids", []) #TODO: ids is deprecated. use objects instead
    result_type = kwargs.get("result", False)
    db          = kwargs.get("db", DB())
    id_view     = kwargs.get("id_view", 0)
    user        = kwargs.get("user", anonymous)
    kwargs["conds"] = kwargs.get("conds", [])
    kwargs["limit"] = kwargs.get("limit", 1000)

    if not user:
        return NebulaResponse(ERROR_UNAUTHORISED)

    start_time = time.time()

    ObjectType = {
                "asset" : Asset,
                "item"  : Item,
                "bin"   : Bin,
                "event" : Event,
                "user"  : User
            }[object_type]

    result = {
            "message" : "Incomplete query",
            "response" : 500,
            "data" : [],
            "count" : 0
        }

    if type(result_type) == list:
        result_format = []
        for i, key in enumerate(result_type):
            form = key.split("@")
            if len(form) == 2:
                result_format.append(json.loads(form[1] or "{}"))
            else:
                result_format.append(None)
            result_type[i] = form[0]

        for response, obj in get_objects(ObjectType, **kwargs):
            result["count"] |= response["count"]
            row = []
            for key, form in zip(result_type, result_format):
                if form is None:
                    row.append(obj[key])
                else:
                    form = form or {}
                    row.append(obj.show(key, **form))
            result["data"].append(row)


    elif result_type == "ids":
        # Result is just array of matching object IDs
        for response, obj in get_objects(ObjectType, **kwargs):
            result["count"] |= response["count"]
            result["data"].append(obj.id)

    else:
        # Result is array of full asset metadata sets
        for response, obj in get_objects(ObjectType, **kwargs):
            result["count"] |= response["count"]
            result["data"].append(obj.meta)

    #
    # response
    #

    result["response"] = 200
    result["message"] = "{} {}s returned in {:.02}s".format(
            len(result["data"]),
            object_type,
            time.time() - start_time
        )
    return result
