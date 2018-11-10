from nebula import *
from cherryadmin import CherryAdminView


class ViewAssets(CherryAdminView):
    def build(self, *args, **kwargs):
        self["name"] = "assets"
        self["title"] = "Assets"
        self["js"] = [
                "/static/js/assets.js"
            ]

        try:
            id_view = int(kwargs["v"])
        except (KeyError, ValueError):
            id_view = min(config["views"])
        query = kwargs.get("q", "")
        page = kwargs.get("p", 1)

        self["id_view"] = id_view
        self["query"] = query
        self["page"] = page


#        try:
        view = config["views"][id_view]
#        except KeyError:
#            loggi
#            return #TODO: Raise 400

        self["columns"] = view["columns"]

        records_per_page = 100

        assets = api_get(
                user = self["user"],
                id_view = id_view,
                fulltext=query or False,
                count=True,
                order="mtime DESC",
                limit=records_per_page,
#                offset=(current_page - 1)*records_per_page
            )

        self["assets"] = [Asset(meta=meta) for meta in assets["data"]]


