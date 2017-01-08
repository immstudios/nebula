from nebula import *
from cherryadmin import CherryAdminView

class ViewPanelDetail(CherryAdminView):
    def build(self, *args, **kwargs):
        self["asset"] = None

        try:
            id_asset = int(kwargs["f"])
        except (KeyError, TypeError, ValueError):
            return

        try:
            active_tab = kwargs["t"]
            if not active_tab in ["m", "p", "t"]:
                raise ValueError
        except (KeyError, ValueError):
            active_tab = "m"
        else:
            self["active_tab"] = active_tab

        db = DB()

        asset = Asset(id_asset)
        self["asset"] = asset

        try:
            fconfig = config["folders"][asset["id_folder"]]
        except:
            log_traceback()
            print asset.meta
        self["meta_set"] = fconfig["meta_set"]


