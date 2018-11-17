from pprint import pformat
import cherrypy

from nebula import *
from cherryadmin import CherryAdminView


def validate_data(context, asset, meta):
    result = {}
    for key in meta:
        value = meta[key]
        meta_type = meta_types[key]
        new_val = None

        if meta_type["class"] in [STRING, TEXT]:
            new_val = value

        elif meta_type["class"] == INTEGER:
            if not value:
                new_val = 0
            else:
                try:
                    new_val = int(value)
                except ValueError:
                    return "Invalid value for key {}".format(key)

        elif meta_type["class"] == NUMERIC:
            if not value:
                new_val = 0
            else:
                try:
                    new_val = float(value)
                    #todo chage float to int
                except ValueError:
                    return "Invalid value for key {}".format(key)

        elif meta_type["class"] == BOOLEAN:
            if value == "1":
                new_val = True
            else:
                new_val = False

        elif meta_type["class"] == DATETIME:
            if not value:
                new_val = 0
            elif meta_type["mode"] == "date":
                try:
                    new_val = datestr2ts(value)
                except Exception:
                    return "Invalid value for key {}".format(key)
                #TODO time

        elif meta_type["class"] == TIMECODE:
            try:
                new_val = tc2s(value, asset.fps)
            except Exception:
                log_traceback()
                return "Invalid value for key {}".format(key)
        elif meta_type["class"] == REGIONS:
            new_val = value
        elif meta_type["class"] == FRACTION:
            new_val = value
        elif meta_type["class"] == SELECT:
            new_val = value
        elif meta_type["class"] == LIST:
            new_val = value
        elif meta_type["class"] == COLOR:
            new_val = value


        if asset[key] != new_val:
            try:
                asset[key] = new_val
            except Exception:
                log_traceback()
                return "Invalid value for key {}".format(key)


    return asset



class ViewDetail(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "detail"
        self["title"] = "Asset detail"
        self["js"] = ["/static/js/detail.js"]

        try:
            id_asset = int(args[-1].split("-")[0])
        except (IndexError, ValueError):
            id_asset = 0

        if not id_asset:
            self["asset"] = False
            return

        asset = Asset(id_asset)
        self["asset"] = asset
        self["title"] = asset["title"]

        id_folder = int(kwargs.get("folder_change", asset["id_folder"]))

        if cherrypy.request.method == "POST":
            meta = validate_data(self.context, asset, kwargs)
            if type(meta) == str:
                self.context.message(meta, level="error")
            else:
                self.context.message("<pre>"+pformat(asset.meta)+"</pre>")


        try:
            fconfig = config["folders"][id_folder]
        except:
            log_traceback()
        self["meta_set"] = fconfig["meta_set"]
        self["id_folder"] = id_folder


        self["extended_keys"] = sorted([k for k in asset.meta if meta_types[k]["ns"] not in ["f","q"] and k not in [l[0] for l in fconfig["meta_set"]]], key=lambda k: meta_types[k]["ns"])
        self["technical_keys"] = sorted([k for k in asset.meta if meta_types[k]["ns"] in ["f","q"] ])
