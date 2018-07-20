#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_set"]

def api_set(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}

    object_type = kwargs.get("object_type", "asset")
    ids  = kwargs.get("objects", [])
    data = kwargs.get("data", {})
    user = User(meta=kwargs["user"])
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

        if object_type == "asset":
            id_folder = data.get("id_folder", False) or obj["id_folder"]
            if not user.has_right("asset_edit", id_folder):
                return {
                        "response" : 403,
                        "message" : "{} is not allowed to edit {} folder".format(
                            user,
                            config["folders"][id_folder]["title"]
                        )
                    }

        changed = False
        for key in data:
            value = data[key]
            old_value = obj[key]
            obj[key] = value
            if obj[key] != old_value:
                changed = True

        validation_script = "" #TODO

        if changed and validation_script:
            logging.debug("Executing validation script")
            exec(validation_script)
            tt = obj.__repr__()
            obj = validate(obj)
            if not isinstance(obj, BaseObject):
                return {
                        "response" : 500,
                        "message" : "Unable to save {}: {}".format(tt, obj)
                    }

        if changed:
            changed_objects.append(obj.id)
            obj.save()
            if object_type == "item" and obj["id_bin"] not in affected_bins:
                affected_bins.append(obj["id_bin"])


    if changed_objects:
        messaging.send("objects_changed", objects=changed_objects, object_type=object_type, user="{}".format(user))

    if affected_bins:
        bin_refresh(affected_bins, db=db)

    return {"response" : 200}

