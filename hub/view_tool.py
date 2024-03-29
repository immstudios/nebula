import cherrypy

from cherryadmin import CherryAdminRawView


class ViewTool(CherryAdminRawView):
    def auth(self, *args, **kwargs):
        return True

    def build(self, *args, **kwargs):
        self.is_raw = False
        self["name"] = "tool"
        self["title"] = "Nebula WebTool"

        try:
            tool_name = args[1]
        except IndexError:
            raise cherrypy.HTTPError(400, "Tool name unspecified")

        try:
            Plugin, title = self["site"]["webtools"].tools[tool_name]
        except KeyError:
            raise cherrypy.HTTPError(404, "No such tool")

        try:
            args = args[2:]
        except IndexError:
            args = []

        plugin = Plugin(self, tool_name)
        self["title"] = title

        if not (plugin.public or self["user"]):
            raise cherrypy.HTTPError(403, "You are not allowed to run this tool")

        body = plugin.build(*args, **kwargs)
        if plugin.native:
            self.is_raw = False
            self["body"] = body
        else:
            self.is_raw = True
            self.body = body
