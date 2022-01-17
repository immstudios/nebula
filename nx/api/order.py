
from nx.helpers import bin_refresh
from nxtools import logging, log_traceback

from nx import (
    NebulaResponse,
    Asset,
    Item,
    DB,
    config,
    anonymous,
    bin_refresh
)

from nebulacore.constants import (
    ERROR_UNAUTHORISED,
    ERROR_ACCESS_DENIED,
    ERROR_BAD_REQUEST
)


__all__ = ["api_order"]

def api_order(**kwargs):
    """
    Changes order of items in bin/rundown, creates new items from assets
    """

    id_channel = kwargs.get("id_channel", 0)
    id_bin = kwargs.get("id_bin", False)
    order = kwargs.get("order", [])
    db = kwargs.get("db", DB())
    user = kwargs.get("user", anonymous)
    initiator = kwargs.get("initiator", None)

    if not user:
        return NebulaResponse(ERROR_UNAUTHORISED)

    if not id_channel in config["playout_channels"]:
        return NebulaResponse(ERROR_BAD_REQUEST, f"No such channel ID {id_channel}")

    playout_config = config["playout_channels"][id_channel]
    append_cond = playout_config.get("rundown_accepts", "True")

    if id_channel and not user.has_right("rundown_edit", id_channel):
        return NebulaResponse(ERROR_ACCESS_DENIED, "You are not allowed to edit this rundown")

    if not (id_bin and order):
        return NebulaResponse(ERROR_BAD_REQUEST, f"Bad \"order\" request<br>id_bin: {id_bin}<br>order: {order}")

    logging.info(f"{user} executes bin_order method")
    affected_bins = [id_bin]
    pos = 1
    rlen = float(len(order))
    for i, obj in enumerate(order):
        object_type = obj["object_type"]
        id_object = obj["id_object"]
        meta = obj["meta"]

        if object_type == "item":
            if not id_object:
                item = Item(db=db)
                item["id_asset"] = obj.get("id_asset", 0)
                item.meta.update(meta)
            else:
                item = Item(id_object, db=db)
                if not item["id_bin"]:
                    logging.error(f"Attempted asset data insertion ({object_type} ID {id_object} {meta}) to item. This should never happen")
                    continue

                if not item:
                    logging.debug(f"Skipping {item}")
                    continue

            if not item["id_bin"] in affected_bins:
                if item["id_bin"]:
                    affected_bins.append(item["id_bin"])

        elif object_type == "asset":
            asset = Asset(id_object, db=db)
            if not asset:
                logging.error(f"Unable to append {object_type} ID {id_object}. Asset does not exist")
                continue
            try:
                can_append = eval(append_cond)
            except Exception:
                log_traceback("Unable to evaluate rundown accept condition: {append_cond}")
                continue
            if not can_append:
                logging.error(f"Unable to append {asset}. Does not match conditions.")
                continue
            item = Item(db=db)
            for key in meta:
                if key in ["id", "id_bin", "id_asset"]:
                    continue
                item[key] = meta[key]
            item["id_asset"] = asset.id
            item.meta.update(meta)
        else:
            logging.error(f"Unable to append {object_type} ID {id_object} {meta}. Unexpected object")
            continue

        if not item or item["position"] != pos or item["id_bin"] != id_bin:
            item["position"] = pos
            item["id_bin"]   = id_bin
            item.save(notify=False) # bin_refresh called later should be enough to trigger rundown reload
        pos += 1


    # Update bin duration
    bin_refresh(affected_bins, db=db, initiator=initiator)

    return NebulaResponse(200)
