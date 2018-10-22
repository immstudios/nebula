from nx import *

__all__ = ["api_actions"]

def api_actions(**kwargs):
    if not kwargs.get("user", None):
        return NebulaResponse(ERROR_UNAUTHORISED)

    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    user = User(meta=kwargs.get("user"))
    if not user:
        return NebulaResponse(ERROR_UNAUTHORISED, "You are not allowed to execute any actions")

    if not ids:
        return NebulaResponse(ERROR_BAD_REQUEST, "No asset selected")

    result = []


    db.query("SELECT id, title, settings FROM actions ORDER BY id ASC")
    for id, title, settings in db.fetchall():
        allow = False
        try:
            cond = xml(settings).find("allow_if").text
        except Exception:
            log_traceback()
            continue

        for id_asset in ids:
            asset = Asset(id_asset, db=db)
            if not eval(cond):
                break
        else:
            if user.has_right("job_control", id):
                result.append((id, title))

    return NebulaResponse(200, data=result)
