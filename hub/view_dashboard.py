from nebula import *
from cherryadmin import CherryAdminView

class ViewDashboard(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "dashboard"
        self["title"] = "Dashboard"
        self["js"] = [
                "/static/js/dashboard.js"
            ]

        db = DB()


        object_counts = {}
        for obj_type in  ["assets", "items", "bins", "events"]:
            db.query("SELECT COUNT(id) FROM {}".format(obj_type))
            object_counts[obj_type] = db.fetchall()[0][0]

        self["object_counts"] = object_counts

