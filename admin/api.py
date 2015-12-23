import os
import cherrypy
import jinja2

from nx import *


class NebulaAPI():
    @cherrypy.expose
    def index(self):
        return "api root"
    
