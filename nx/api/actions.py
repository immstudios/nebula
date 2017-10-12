from nx import *

__all__ = ["api_actions"]

def api_actions(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}

    ids = kwargs.get("ids", [])
    user = kwargs.get("user", anonymous)
    db = kwargs.get("db", DB())

    if not ids:
        return {"response" : 400, "message" : "No asset selected"}

    result = []

    db.query("SELECT id, title, settings FROM actions ORDER BY id_action ASC")
    for id, title, settings in db.fetchall():
        try:
            cond = xml(cfg).find("allow_if").text
        except Exception:
            log_traceback()
            continue

        for id_asset in ids:
            asset = Asset(id_asset, db=db)
            if not eval(cond):
                break
        else:
            if user.has_right("job_control", id_action):
                result.append((id_action, title))

    return {'response' : 200, 'message' : 'OK', 'data' : result }
