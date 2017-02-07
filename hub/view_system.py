from nebula import *
from cherryadmin import CherryAdminView

class ViewSystemSettings(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_settings"
        self["title"] = "Settings"
        self["js"] = []
        db = DB()
        db.query("SELECT key, value FROM settings ORDER BY key")
        self["data"] = db.fetchall()

class ViewSystemStorages(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_storages"
        self["title"] = "Storages"
        self["js"] = []

class ViewSystemFolders(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_folders"
        self["title"] = "Folders"
        self["js"] = []

class ViewSystemViews(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_views"
        self["title"] = "Views"
        self["js"] = []

class ViewSystemChannels(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_channels"
        self["title"] = "Channels"
        self["js"] = []

class ViewSystemActions(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_actions"
        self["title"] = "Actions"
        self["js"] = []

class ViewSystemUsers(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_users"
        self["title"] = "Users"
        self["js"] = []
        db = DB()
        db.query("SELECT id, meta FROM users ORDER BY id")
        self["data"] = [User(meta=meta) for id, meta in db.fetchall()]

class ViewSystemServices(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "system_services"
        self["title"] = "Services"
        self["js"] = []
        services = []
        db = DB()
        db.query("SELECT id, service_type, host, title, autostart, state, last_seen FROM services ORDER BY id")
        for id, service_type, host, title, autostart, state, last_seen in db.fetchall():
            service = {
                    "id" : id,
                    "service_type" : service_type,
                    "host" : host,
                    "title" : title,
                    "autostart" : autostart,
                    "state" : state,
                    "last_seen" : last_seen
                }
            services.append(service)
        self["data"]  = services
