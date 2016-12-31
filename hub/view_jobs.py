from nebula import *
from cherryadmin import CherryAdminView


class ViewJobs(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "jobs"
        self["title"] = "Jobs"
        self["js"] = [
                "/static/js/jobs.js"
            ]

