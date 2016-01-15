import os
import time
import json
import cherrypy

from nx import *

import api_system
import api_assets
import api_items

from .api_auth import APIAuth

api_headers = [
        ["Content-Type", "application/json"],
        ["Connection", "keep-alive"],
        ["Cache-Control", "no-cache"],
        ["Access-Control-Allow-Origin", "*"]
    ]

class NebulaAPI():
    def __init__(self):
        self.auth = APIAuth()
        self.methods = {}
        for module in [api_system, api_assets, api_items]:
            for method in dir(module):
                if not method.startswith("api_"):
                    continue
                method_title = method[4:]
                module_name = module.__name__.split(".")[-1]
#TODO: USE imp here
                exec ("self.methods['{}'] = {}.{}".format(method_title, module_name, method ))
                logging.debug("Enabling method {}".format(method_title))


    @cherrypy.expose
    def index(self, **kwargs):
        print (kwargs)
        auth_key = kwargs.get("auth_key", False)
        method = kwargs.get("method", False)
        params = kwargs.get("params", "{}")
        params = json.loads(params)

        if not (method and auth_key):
            response, data = 400, "Bad request (code #0000)"
        elif method == "login":
            response, data = self.auth.login(auth_key, **params)
        elif method == "logout":
            response, data = self.auth.logout(auth_key)
        else:
            user = self.auth[auth_key]
            if not user:
                response, data = 403, "Not logged in (code #0001)"
            elif method in self.methods:
                try:
                    response, data = self.methods[method](user, **params)
                except:
                    response = 500
                    data = log_traceback("Error occured during query {}".format(method))
            else:
                response, data = 503, "Not implemented (code #0002)"

        for h, v in api_headers:
            cherrypy.response.headers[h] = v
        cherrypy.response.status = response
        return json.dumps(data)
