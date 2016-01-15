import os
import cherrypy
import jinja2

from nx import *
from nx.objects import User, get_user


class NebulaAdmin():
    def __init__(self):
        template_root = os.path.join(config["nebula_root"], "admin", "templates")
        self.jinja = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_root)
            )

    @cherrypy.expose
    def index(self):
        id_user = cherrypy.session.get("id_user", 0)
        if not id_user:
            tpl = self.jinja.get_template("login.html")
        else:
            tpl = self.jinja.get_template("dashboard.html")
        context={}
        return tpl.render(**context)

    @cherrypy.expose
    def login(self, login, password, **kwargs):
        user = get_user(login, password)
        if user:
            cherrypy.session["id_user"] = user.id
        else:
            cherrypy.session["id_user"] = 0
        raise cherrypy.HTTPRedirect(kwargs.get("from_page", "/"))

    @cherrypy.expose
    def logout(self):
        cherrypy.session["id_user"] = False
        raise cherrypy.HTTPRedirect("/")


    ##
    # Views
    ##
