import cherrypy

from nx import *

class NebulaAdmin():
    @cherrypy.expose
    def index(self):
        return "hello"



class Admin():
    def __init__(self):
        cherrypy.config.update({
            'server.socket_host': config.get("admin_host", "127.0.0.1"),
            'server.socket_port': config.get("admin_port", 8080),
            })

        cherrypy.engine.subscribe('start', self.start)
        cherrypy.tree.mount(NebulaAdmin(), "/")

        cherrypy.engine.subscribe('stop', self.stop)
        cherrypy.engine.start()

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    @property
    def is_running(self):
        cherrypy.engine

    def shutdown(self):
        cherrypy.engine.exit()
