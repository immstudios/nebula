#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_set"]

def api_set(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}

    object_type = kwargs.get("object_type", "asset")
    ids  = kwargs.get("ids", [])
    echo = kwargs.get("echo", False)
    data = kwargs.get("data", {})
    user = kwargs.get("user", anonymous)
    db   = kwargs.get("db", DB())

    if not (data and ids):
        return {"response" : 304, "message" : "No object created or modified"}

    object_type_class = {
                "asset" : Asset,
                "item"  : Item,
                "bin"   : Bin,
                "event" : Event,
            }[object_type]

    changed_objects = []
    affected_bins = []

    for id_object in ids:
        obj = object_type_class(id_object, db=db)
        changed = False
        validator_script = None

        if object_type == "asset":
            id_folder = data.get("id_folder", False) or obj["id_folder"]

            if not user.has_right("asset_edit", id_folder):
                return {"response" : 403, "message" : "{} is not allowed to edit asset in folder {}".format(user, id_folder)}

            db.query("SELECT validator FROM nx_folders WHERE id_folder=%s", [id_folder])
            try:
                validator_script = db.fetchall()[0][0]
            except IndexError:
                validator_script = None

            # New asset needs create_script and id_folder
            if not id_object:
                if not validator_script:
                    return {"response" : 400, "message" : "It is not possible create asset in this folder"}

                if not data["id_folder"]:
                    return {"response" : 400, "message" : "You must select asset folder"}

        changed = False
        messages = []
        for key in data:
            value = data[key]
            old_value = obj[key]
            obj[key] = value

            if obj[key] != old_value:
                changed = True

        if changed and validator_script:
            logging.debug("Executing validation script")
            exec(validator_script)
            obj = validate(obj)
            if not isinstance(obj, BaseObject):
                return {"response" : 500, "message" : "Unable to save {}: {}".format(tt, obj)}

        if changed:
            changed_objects.append(obj.id)
            obj.save(notify=False)
            if object_type == "item" and obj["id_bin"] not in affected_bins:
                affected_bins.append(obj["id_bin"])
            for message in messages:
                logging.info(message)

    if affected_bins:
        bin_refresh(affected_bins, db=db)

    messaging.send("objects_changed", objects=changed_objects, object_type=object_type, user="{}".format(user))
    return {"response" : 200}

