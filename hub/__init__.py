from cherryadmin import CherryAdmin

from nebula import *

from .view_dashboard import ViewDashboard
from .view_mam import ViewMAM
from .view_panel_browser import ViewPanelBrowser
from .view_panel_detail import ViewPanelDetail
from .view_panel_rundown import ViewPanelRundown
from .view_panel_scheduler import ViewPanelScheduler


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
            "css" : [
                    "/static/css/main.css"
                ],
            "mam_modules": [
                    ["detail", "Asset"],
                    ["rundown", "Rundown"],
                    ["scheduler", "Scheduler"]
                ],

            "meta_types" : meta_types,
        }

    def __getitem__(self, key):
        if key in self.context:
            return self.context[key]
        return config[key]


def site_context_helper():
    return SiteContext()


def page_context_helper():
    return {}


hub_config = {
        "static_dir" : config.get("hub_static_dir", "hub/static"),
        "templates_dir" : config.get("hub_templates_dir", "hub/templates"),
        "login_helper" : login_helper,
        "site_context_helper" : site_context_helper,
        "page_context_helper" : page_context_helper,
        "blocking" : True,
        "views" : {
                "index" : ViewDashboard,
                "mam" : ViewMAM,
                "panel_browser" : ViewPanelBrowser,
                "panel_detail" : ViewPanelDetail,
                "panel_rundown" : ViewPanelRundown,
                "panel_scheduler" : ViewPanelScheduler,
            },
        "api_methods" : {
                "get" : api_get,
            }
    }

