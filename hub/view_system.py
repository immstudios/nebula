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
        db = DB()
        db.query("SELECT id, settings FROM storages ORDER BY id")
        self["data"] = db.fetchall()


class ViewSystemFolders(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "folders"
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
