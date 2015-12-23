import os
import cherrypy
import jinja2

from nx import *

from .admin import NebulaAdmin
from .api import NebulaApi

class Admin():
    def __init__(self):
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
                'tools.sessions.on': True, 
                 }, 
            } 
        
        cherrypy.config.update({
            'server.socket_host': config.get("admin_host", "127.0.0.1"),
            'server.socket_port': config.get("admin_port", 8080),
            'log.screen' : False
            })

        cherrypy.engine.subscribe('start', self.start)
        cherrypy.tree.mount(NebulaAdmin(), "/", self.admin_config)
        cherrypy.tree.mount(NebulaAPI(), "/api", self.admin_config)

        cherrypy.engine.subscribe('stop', self.stop)
        cherrypy.engine.start()

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def shutdown(self):
        cherrypy.engine.exit()
