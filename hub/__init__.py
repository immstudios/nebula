import imp

from cherryadmin import CherryAdmin

from nebula import *

from .webtools import webtools

from .view_dashboard import ViewDashboard
from .view_assets import ViewAssets
from .view_detail import ViewDetail
from .view_jobs import ViewJobs
from .view_tool import ViewTool
from .view_services import ViewServices
from .view_passreset import ViewPassReset
from .view_profile import ViewProfile

logging.user = "hub"


__all__ = [
        "CherryAdmin",
        "hub_config",
    ]

def login_helper(login, password):
    user = get_user(login, password)
    if not user:
        return False
    return user.meta



class SiteContext(object):
    context = {
            "name" : config["site_name"],
            "js" : [
                    "/static/js/vendor.min.js",
                    "/static/js/main.js"
                ],
            "css" : ["/static/css/main.css"],
            "meta_types" : meta_types,
            "webtools" : webtools
        }

    def __getitem__(self, key):
        if key in self.context:
            return self.context[key]
        return config[key]


def site_context_helper():
    return SiteContext()


def page_context_helper():
    return {}

static_dir = config.get("hub_static_dir", os.path.join(config["nebula_root"], "hub", "static"))
templates_dir = config.get("hub_templates_dir", os.path.join(config["nebula_root"], "hub", "templates"))

hub_config = {
        "host" : config.get("hub_host", "0.0.0.0"),
        "port" : config.get("hub_port", 8080),
        "static_dir" : static_dir,
        "templates_dir" : templates_dir,
        "login_helper" : login_helper,
        "site_context_helper" : site_context_helper,
        "page_context_helper" : page_context_helper,
        "sessions_dir" : os.path.join("/tmp", config["site_name"] + "-sessions"),
        "blocking" : True,
        "minify_html" : True,
        "views" : {
                "index"    : ViewDashboard,
                "assets"   : ViewAssets,
                "detail"   : ViewDetail,
                "jobs"     : ViewJobs,
                "tool"     : ViewTool,
                "services" : ViewServices,
                "passreset" : ViewPassReset,
                "profile"   : ViewProfile,
            },

        "api_methods" : {
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
            }
    }

