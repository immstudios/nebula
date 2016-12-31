from nebula import *
from cherryadmin import CherryAdminView

class ViewPanelRundown(CherryAdminView):
    def build(self, *args, **kwargs):
        rundown_start_time = 1482901200
        data = get_rundown(1, rundown_start_time)
        self["columns"] = ["rundown_symbol", "title", "rundown_scheduled", "rundown_broadcast"]
        self["rundown"] = data
