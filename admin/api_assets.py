from nx import *
from nx.objects import *

def api_browse(user, **kwargs):
    db = DB()

    conds = []

    id_view = kwargs.get("view", 1)
    view_config = config["views"][id_view]

    if "folders" in view_config:
        conds.append("id_folder IN ({})".format(view_config["folders"]))
    if "media_types" in view_config:
        conds.append("media_type IN ({})".format(view_config["media_types"]))
    if "content_types" in view_config:
        conds.append("content_type IN ({})".format(view_config["content_types"]))
    if "origins" in view_config:
        conds.append("origin IN ({})".format(view_config["origins"]))
    if "statuses" in view_config:
        conds.append("status IN ({})".format(view_config["statuses"]))
    if "query" in view_config:
        conds.append("id_object in ({})".format(view_config["query"]))

    # TODO: PLEASE REWRITE ME
    if kwargs.get("fulltext", False):
        fulltext_base = "id_object IN (SELECT id_object FROM nx_meta WHERE object_type=0 AND {})"
        element_base  = "unaccent(value) ILIKE unaccent('%{}%')"
        fq = kwargs["fulltext"].encode("utf-8").replace("'", "''")
        fulltext_cond = " AND ".join([element_base.format(elm) for elm in fq.split()])
        conds.append(fulltext_base.format(fulltext_cond))

    query_conditions = " WHERE {}".format(" AND ".join(conds)) if conds else ""
    query = "SELECT id_object, mtime FROM nx_assets{}".format(query_conditions)

    db.query(query)
    return 200, {"result": db.fetchall(), "asset_data":[]}


def api_get_assets(user, **kwargs):
    asset_ids = kwargs.get("asset_ids", [])
    db = DB()
    result = []
    for id_asset in asset_ids:
        asset = Asset(id_asset, db=db)
        result.append(asset.meta)
    return 200, result



def api_actions(user, **kwargs):
    i = 0
    assets = kwargs.get("assets", [])
    if not assets:
        return 400, "No asset selected"

    result = []
    db = DB()
    db.query("SELECT id_action, title, config FROM nx_actions ORDER BY id_action ASC")
    for id_action, title, cfg in db.fetchall():
        try:
            cond = ET.XML(cfg).find("allow_if").text
        except:
            continue
        for id_asset in assets:
            asset = Asset(id_asset, db=db)
            if not eval(cond):
                break
        else:
            if user.has_right("job_control", id_action):
                result.append((id_action, title))
    return 200, result



def api_send_to(user, **kwargs):
    id_action = kwargs.get("id_action", False)
    settings  = kwargs.get("settings", {})
    restart_existing = kwargs.get("restart_existing", True)

    if not id_action:
        return 400, "Bad request in send to"

    if not user.has_right("job_control", id_action):
        return 403, "Not authorised "

    logging.info("{} is starting action {} for following assets: {}".format(user, id_action, kwargs.get("objects", [])))

    db = DB()
    for id_object in kwargs.get("objects", []):
        send_to(id_object, id_action, settings={}, id_user=user.id, restart_existing=restart_existing, db=db)[1]
    return 200, "OK"



def api_set_meta(user, **kwargs):
    objects = [int(id_object) for id_object in kwargs.get("objects",[])]
    object_type = kwargs.get("object_type","asset")
    data = kwargs.get("data", {})
    db = DB()
    changed_objects = []
    affected_bins = []
    for id_object in objects:

        obj = {
            "asset" : Asset,
            "item"  : Item,
            "bin"   : Bin,
            "event" : Event,
            }[object_type](id_object, db=db)


        validator_script = None
        if object_type == "asset":
            id_folder = data.get("id_folder", False) or obj["id_folder"]

            if not user.has_right("asset_edit", id_folder):
                return 403, "Unauthorised (edit asset in folder {})".format(id_folder)

            db.query("SELECT validator FROM nx_folders WHERE id_folder=%s", [id_folder])
            try:
                validator_script = db.fetchall()[0][0]
            except:
                validator_script = None

            # New asset need create_script and id_folder
            if not id_object:

                if not user.has_right("asset_edit", id_folder):
                    msg = "Unauthorised (create asset in folder {})".format(id_folder)
                    logging.warning(msg)
                    return 403, msg

                if not validator_script:
                    msg = "It is not possible create asset in this folder."
                    logging.warning(msg)
                    return 400, msg

                if not data["id_folder"]:
                    msg = "You must select asset folder"
                    logging.warning(msg)
                    return 400, msg

        changed = False
        messages = []
        for key in data:
            value = data[key]
            old_value = obj[key]
            obj[key] = value
            if obj[key] != old_value:

                with fuckit:
                    v1 = old_value
                    v1 = v1.encode("utf-8")

                with fuckit:
                    v2 = obj[key]
                    v2 = v2.encode("utf-8")

                messages.append("{} set {} {} from {} to {}".format(user, obj, key, v1, v2))
                changed = True

        if changed and validator_script:
            logging.debug("Executing validation script")
            tt = "{}".format(obj)
            exec(validator_script)
            obj = validate(obj)
            if not isinstance(obj, BaseObject):
                logging.warning("Unable to save {}: {}".format(tt, obj))
                return 400, obj

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
    return 200, obj.meta




def api_trash(user, **kwargs):
    objects = [int(id_object) for id_object in kwargs.get("objects",[])]
    db = DB()
    for id_asset in objects:
        asset = Asset(id_asset, db=db)
        if user.has_right("asset_edit", asset["id_folder"]):
            logging.info("{} is trashing {}".format(user, asset))
            asset["status"] = TRASHED
            asset.save()
    return 200, "OK"


def api_untrash(user, **kwargs):
    objects = [int(id_object) for id_object in kwargs.get("objects",[])]
    db = DB()
    for id_asset in objects:
        asset = Asset(id_asset, db=db)
        if user.has_right("asset_edit", asset["id_folder"]):
            logging.info("{} is untrashing {}".format(user, asset))
            asset["status"] = RESET
            asset.save()
    return 200, "OK"


def api_archive(user, **kwargs):
    objects = [int(id_object) for id_object in kwargs.get("objects",[])]
    db = DB()
    for id_asset in objects:
        asset = Asset(id_asset, db=db)
        if user.has_right("asset_edit", asset["id_folder"]):
            logging.info("{} is archiving {}".format(user, asset))
            asset["status"] = ARCHIVED
            asset.save()
    return 200, "OK"


def api_unarchive(user, **kwargs):
    objects = [int(id_object) for id_object in kwargs.get("objects",[])]
    db = DB()
    for id_asset in objects:
        asset = Asset(id_asset, db=db)
        if user.has_right("asset_edit", asset["id_folder"]):
            logging.info("{} is unarchiving {}".format(user, asset))
            asset["status"] = RESET
            asset.save()
    return 200, "OK"
