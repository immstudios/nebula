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

        cherrypy.tree.mount(NebulaAdmin(), "/")
        cherrypy.engine.start()

    def shutdown(self):
        cherrypy.engine.exit()
