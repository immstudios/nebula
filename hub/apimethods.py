import imp
from nebula import *


class APIMethods(dict):
    def __init__(self):
        super(APIMethods, self).__init__()
        self.load()

    def load(self):
        self.clear()
        self.update({
                "get"      : api_get,
                "set"      : api_set,
                "delete"   : api_delete,
                "settings" : api_settings,
                "rundown"  : api_rundown,
                "order"    : api_order,
                "schedule" : api_schedule,
                "jobs"     : api_jobs,
                "playout"  : api_playout,
                "actions"  : api_actions,
                "send"     : api_send,
                "solve"    : api_solve,
                "system"   : api_system,
            })
        logging.info("Reloading API methods")
        apidir = get_plugin_path("api")
        if not apidir:
            return


api_methods = APIMethods()