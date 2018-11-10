from nebula import *
from cherryadmin import CherryAdminView


class ViewDetail(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "detail"
        self["title"] = "Asset detail"
        self["js"] = [
            ]

        try:
            id_asset = int(args[-1].split("-")[0])
        except (IndexError, ValueError):
            id_asset = 0

        mode = kwargs.get("mode", "full")
        self["mode"] = mode
        print("MODE", mode)
        if mode == "dialog":
            self["template"] = "_dialog.html"
        else:
            self["template"] = "_base.html"

        if not id_asset:
            self["asset"] = False
            return

        asset = Asset(id_asset)
        self["asset"] = asset
        self["title"] = asset["title"]

        try:
            fconfig = config["folders"][asset["id_folder"]]
        except:
            log_traceback()
        self["meta_set"] = fconfig["meta_set"]


        self["extended_keys"] = sorted([k for k in asset.meta if k not in [l[0] for l in fconfig["meta_set"]]], key=lambda k: meta_types[k]["ns"])
