import os
import cherrypy
import jinja2

from nx import *

from .admin import NebulaAdmin
from .api import NebulaAPI

class Admin():
    def __init__(self, blocking=False):
        self.is_running = False
        self.admin_config = {
            '/': {
                'tools.sessions.on': True,
                'tools.staticdir.root': os.path.join(config["nebula_root"], "admin")
                 },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': "static"
                },
            }
        self.api_config = {
            '/': {
                'tools.sessions.on' : True,
                'tools.trailing_slash.on' : False
                 },
            }

        cherrypy.config.update({
            'server.socket_host': config.get("admin_host", "0.0.0.0"),
            'server.socket_port': config.get("admin_port", 80),
#            'log.screen' : False
            })

        cherrypy.engine.subscribe('start', self.start)
        cherrypy.tree.mount(NebulaAdmin(), "/", self.admin_config)
        cherrypy.tree.mount(NebulaAPI(), "/api", self.admin_config)

        cherrypy.engine.subscribe('stop', self.stop)
        cherrypy.engine.start()
        if blocking:
            cherrypy.engine.block()

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def shutdown(self):
        cherrypy.engine.exit()
