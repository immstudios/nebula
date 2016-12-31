from nebula import *
from cherryadmin import CherryAdminView

class ViewPanelDetail(CherryAdminView):
    def build(self, *args, **kwargs):
        try:
            id_asset = int(kwargs["f"])
        except KeyError, TypeError:
            return #TODO: return error message

        db = DB()

        asset = Asset(id_asset)
        self["asset"] = asset

        try:
            fconfig = config["folders"][asset["id_folder"]]
        except:
            log_traceback()
            print asset.meta
        self["meta_set"] = fconfig["meta_set"]


