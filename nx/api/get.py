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

    conds = []
    for cond in raw_conds:
        for col in ObjectType.db_cols:
            if conds.startswith(col):
                conds.append(raw_cond)
                break
        conds.append("meta->>"+cond)

    if fulltext:
        ft = slugify(fulltext, make_set=True)
        for word in ft:
            conds.append("id IN (SELECT id FROM ft WHERE object_type={} AND value LIKE '{}%')".format(ObjectType.object_type_id, word))

    conds = "WHERE " + " AND ".join(conds) if conds else ""
    counter = ", count(*) OVER() AS full_count" if do_count else ", 0"

    q = "SELECT id, meta{} FROM {} {}".format(counter, ObjectType.table_name, conds)
    q += " LIMIT {}".format(limit) if limit else ""
    q += " OFFSET {}".format(offset) if offset else ""

    logging.debug("Executing get query:", q)
    db.query(q)

    for id, meta, count in db.fetchall():
        yield {"count": count}, ObjectType(meta=meta, db=db)





def api_get(**kwargs):
    object_type = kwargs.get("object_type", "asset")
    ids         = kwargs.get("ids", [])
    result_type = kwargs.get("result", False)
    user        = kwargs.get("user", anonymous)
    db          = kwargs.get("db", DB())

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

    if ids:
        # We do not do database lookup. Just returning objects by their ids
        result["data"] = [ObjectType(id, db=db).meta for id in ids]
        result["count"] = len(result["data"])

    else:
        # We actually search the database
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
