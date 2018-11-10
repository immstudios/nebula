import cherrypy

from nebula import *
from cherryadmin import CherryAdminView


class ViewProfile(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "profile"
        self["title"] = "User profile"
        self["js"] = []

        db = DB()

        print(">>>", kwargs)

        if "password" in kwargs or "full_name" in kwargs:
            user = User(self["user"]["id"], db=db)
            print("modify user", user)
            if kwargs.get("full_name", ""):
                user["full_name"] = kwargs["full_name"]
            if kwargs.get("password", ""):
                user.set_password(kwargs["password"])
            user.save()

            self.context["user"] = user.meta
            cherrypy.session["user_data"] = user.meta
            self.context.message("User profile saved")

        self["rights"] = [
                ["asset_edit",      "Edit assets", "folders"],
                ["asset_create",    "Create assets", "folders"],
                ["rundown_view",    "View rundown", "playout_channels"],
                ["rundown_edit",    "Edit rundown", "playout_channels"],
                ["scheduler_view",  "View scheduler", "playout_channels"],
                ["scheduler_edit",  "Modify scheduler", "playout_channels"],
                ["job_control",     "Control jobs", "action"],
                ["service_control", "Control services", "services"],
                ["mcr",             "Control playout", "playout_channels"],
            ]

        db.query("SELECT meta FROM users WHERE meta->>'is_admin' = 'true'")
        self["admins"] = [User(meta=meta) for meta, in db.fetchall()]
        self["user"] = User(meta=self.context["user"])


