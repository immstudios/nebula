from nebula import *
from cherryadmin import CherryAdminView

class ViewPanelDetail(CherryAdminView):
    def build(self, *args, **kwargs):
        try:
            id_asset = int(kwargs["id"])
        except KeyError, TypeError:
            return #TODO: return error message

        asset = Asset(id_asset)
        self["asset"] = asset

        fconfig = config["folders"][asset["id_folder"]]
        self["meta_set"] = fconfig["meta_set"]


