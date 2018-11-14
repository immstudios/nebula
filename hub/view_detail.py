from pprint import pformat
import cherrypy

from nebula import *
from cherryadmin import CherryAdminView


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
            self.context.message("<pre>"+pformat(kwargs)+"</pre>")


        try:
            fconfig = config["folders"][id_folder]
        except:
            log_traceback()
        self["meta_set"] = fconfig["meta_set"]
        self["id_folder"] = id_folder


        self["extended_keys"] = sorted([k for k in asset.meta if k not in [l[0] for l in fconfig["meta_set"]]], key=lambda k: meta_types[k]["ns"])
