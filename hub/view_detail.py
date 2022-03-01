import cherrypy
from cherryadmin import CherryAdminView

from nxtools import logging, log_traceback, datestr2ts, tc2s
from nx.db import DB
from nx.core import config
from nx.objects import Asset
from nx.enum import MetaClass
from nx.api import api_set, api_actions


def validate_data(context, asset, meta):
    changed = False
    for key in meta:
        value = meta[key]
        meta_type = asset.meta_types[key]
        new_val = None

        if meta_type["class"] in [MetaClass.STRING, MetaClass.TEXT]:
            new_val = value

        elif meta_type["class"] == MetaClass.INTEGER:
            if not value:
                new_val = 0
            else:
                try:
                    new_val = int(value)
                except ValueError:
                    return f"Invalid value for key {key}"

        elif meta_type["class"] == MetaClass.NUMERIC:
            if not value:
                new_val = 0
            else:
                try:
                    new_val = float(value)
                    # TODO: chage float to int
                except ValueError:
                    return f"Invalid value for key {key}"

        elif meta_type["class"] == MetaClass.BOOLEAN:
            if value == "1":
                new_val = True
            else:
                new_val = False

        elif meta_type["class"] == MetaClass.DATETIME:
            if not value:
                new_val = 0
            elif meta_type["mode"] == "date":
                try:
                    new_val = datestr2ts(value)
                except Exception:
                    log_traceback()
                    return "Invalid value {} for key {}".format(value, key)
                # TODO: time

        elif meta_type["class"] == MetaClass.TIMECODE:
            try:
                new_val = tc2s(value, asset.fps)
            except Exception:
                log_traceback()
                return "Invalid value for key {}".format(key)
        elif meta_type["class"] == MetaClass.OBJECT:
            new_val = value
        elif meta_type["class"] == MetaClass.FRACTION:
            new_val = value
        elif meta_type["class"] == MetaClass.SELECT:
            new_val = value
        elif meta_type["class"] == MetaClass.LIST:
            new_val = value
        elif meta_type["class"] == MetaClass.COLOR:
            new_val = value

        if asset[key] != new_val:
            changed = True
            try:
                asset[key] = new_val
            except Exception:
                log_traceback()
                return "Invalid value for key {}".format(key)

    if not changed:
        return "No change"
    return None


class ViewDetail(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "detail"
        self["title"] = "Asset detail"
        self["js"] = ["/static/js/vendor/resumable.js", "/static/js/detail.js"]

        try:
            id_asset = int(args[-1].split("-")[0])
        except (IndexError, ValueError):
            id_asset = 0

        db = DB()

        if not id_asset:
            if kwargs.get("new_asset", False):
                asset = Asset(db=db)
                asset["id_folder"] = min(config["folders"].keys())
                self["new_asset"] = True
            else:
                self["asset"] = False
                raise cherrypy.HTTPError(status=404, message="Asset not found")
        else:
            asset = Asset(id_asset, db=db)
            logging.debug(asset)
            if not asset.id:
                raise cherrypy.HTTPError(status=404, message="Asset not found")

        id_folder = int(kwargs.get("folder_change", asset["id_folder"]))
        if id_folder != asset["id_folder"]:
            asset["id_folder"] = id_folder

        if cherrypy.request.method == "POST":
            error_message = validate_data(self.context, asset, kwargs)
            if error_message:
                self.context.message(error_message, level="error")
            else:
                response = api_set(
                    user=self["user"],
                    objects=[asset.id],
                    data={k: asset[k] for k in kwargs},
                    db=db,
                )
                if response.is_success:
                    self.context.message("Asset saved")
                else:
                    self.context.message(response.message, level="error")
                asset = Asset(id_asset, db=db)  # reload after update

        try:
            fconfig = config["folders"][id_folder]
        except Exception:
            self.context.message("Unknown folder ID", level="error")
            fconfig = config["folders"][min(config["folders"].keys())]

        # Get available actions
        actions = api_actions(user=self["user"], db=db, ids=[id_asset])

        self["asset"] = asset
        self["title"] = asset["title"] if asset.id else "New asset"
        self["id_folder"] = id_folder
        self["main_keys"] = fconfig["meta_set"]
        self["extended_keys"] = sorted(
            [
                k
                for k in asset.meta
                if k in asset.meta_types
                and asset.meta_types[k]["ns"] not in ["f", "q"]
                and k not in [mlist[0] for mlist in fconfig["meta_set"]]
            ],
            key=lambda k: asset.meta_types[k]["ns"],
        )

        self["technical_keys"] = sorted(
            [k for k in asset.meta if asset.meta_types[k]["ns"] in ["f", "q"]]
        )
        self["actions"] = actions.data if actions.is_success else []
