from cherryadmin import CherryAdminView

class ViewDashboard(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "dashboard"
        self["title"] = "Dashboard"
        self["js"] = [
                "/static/js/dashboard.js"
            ]

