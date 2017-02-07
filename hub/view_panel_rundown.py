from nebula import *
from cherryadmin import CherryAdminView

class ViewPanelRundown(CherryAdminView):
    def build(self, *args, **kwargs):

        try:
            id_channel = int(kwargs["c"])
            if not id_channel in config["playout_channels"].keys():
                raise Exception
        except:
            id_channel = min(config["playout_channels"].keys())

        playout_config = config["playout_channels"][id_channel]
        sh, sm = playout_config.get("day_start", [6, 0])

        try:
            rundown_date = kwargs["d"]
            if not rundown_date:
                raise Exception
            rundown_start_time = datestr2ts(rundown_date, hh=sh, mm=sm)
        except Exception:
            # default today
            rundown_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            rundown_start_time = datestr2ts(rundown_date, hh=sh, mm=sm)


        data = get_rundown(id_channel, rundown_start_time)
        self["columns"] = ["rundown_symbol", "title", "rundown_scheduled", "rundown_broadcast"]
        self["rundown"] = data
        self["id_channel"] = id_channel
