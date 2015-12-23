import os
import cherrypy
import jinja2

from nx import *


class NebulaAdmin():
    def __init__(self):
        template_root = os.path.join(config["nebula_root"], "admin", "templates")
        self.jinja = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_root)
                )

    @cherrypy.expose
    def index(self):
        return "hello"
