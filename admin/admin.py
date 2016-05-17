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

    def context(self, **kwargs):
        context = {
                "site" : {}
                "user" : {}
                "nebula" : {}
            }
        context.update(kwargs)
        return context

    def render(self, template, **kwargs):
        return template.render(template, context(**kwargs))

    @cherrypy.expose
    def index(self):
        print cherrypy.session
        id_user = cherrypy.session.get("id_user", 0)
        logging.debug("Index requested by {}".format(id_user))
        context={}
        if not id_user:
            tpl = self.jinja.get_template("login.html")
        else:
            tpl = self.jinja.get_template("dashboard.html")
            context["columns"] = "title", "duration", "genre", "id_folder"
            context["assets"] = list(browse(genre="Horror"))
        return self.render(tpl, **context)

    @cherrypy.expose
    def login(self, login, password, **kwargs):
        user = get_user(login, password)
        print ">>>", user.meta
        if user:
            cherrypy.session["id_user"] = user.id
            logging.goodnews("{} is logged in : ID {}".format(login, user.id))
        else:
            logging.error("{} login failed".format(login))
            cherrypy.session["id_user"] = 0
        raise cherrypy.HTTPRedirect(kwargs.get("from_page", "/"))

    @cherrypy.expose
    def logout(self):
        cherrypy.session["id_user"] = False
        raise cherrypy.HTTPRedirect("/")


    ##
    # Views
    ##

    @cherrypy.expose
    def browser(self):
        pass

    @cherrypy.expose
    def jobs(self):
        pass

    @cherrypy.expose
    def services(self):
        pass

    @cherrypy.expose
    def config(self):
        pass
