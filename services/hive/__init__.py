from nx import *
from nx.services import BaseService
from nx.objects import *

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import cgi
import thread

import hive_assets
import hive_system
import hive_items
import hive_dramatica

reload(sys)
sys.setdefaultencoding('utf-8')

REQUIRED_PROTOCOL = 140000

class Sessions():
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        db = DB()
        db.query("SELECT id_user FROM nx_sessions WHERE key=%s", [key])
        try:
            user = User(db.fetchall()[0][0])
            return user
        except IndexError:
            return False

    def __delitem__(self, key):
        if key in self.data:
            del(self.data[key])

    def login(self, auth_key, params):
        if params.get("protocol", 0) < REQUIRED_PROTOCOL:
            return [400, "Your Firefly version is outdated.\nPlease download latest update from support website."]

        if self[auth_key]:
            return [200, "Already logged in"]

        if params.get("login") and params.get("password"):
            db = DB()
            user = get_user(params["login"], params["password"], db=db)
            if user:
                db.query("INSERT INTO nx_sessions (key, id_user, host, ctime, mtime) VALUES (%s, %s , %s, %s, %s)", [ auth_key, user.id, params.get("host", "unknown"), time.time(), time.time()])
                db.commit()
                return [200, "Logged in"]
            else:
                return [403, "Incorrect login/password combination"]

        else:
            return [403, "Not logged in"]


    def logout(self, auth_key):
        user = self[auth_key]
        if not user:
            return [403, "Not logged in"]
        db = DB()
        db.query("DELETE FROM nx_sessions WHERE key = %s", [auth_key])
        db.commit()
        del self[auth_key]
        return [200, "ok"]





class HiveHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        pass

    def _do_headers(self,mime="application/json",response=200,headers=[]):
        self.send_response(response)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        for h in headers:
            handler.send_header(h[0],h[1])
        self.send_header('Content-type', mime)
        self.end_headers()

    def _echo(self,istring):
        self.wfile.write(istring)

    def result(self, response, data, mime="application/json"):
        self._do_headers(mime=mime, response=response)
        if data:
            self._echo(data)
        else:
            self._echo(False)

    @property
    def sessions(self):
        return self.server.service.sessions


    def do_POST(self):
        start_time =  time.time()

        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            logging.error("No post data")
            self.result(ERROR_BAD_REQUEST)
            return

        try:
            method   = postvars["method"][0]
            auth_key = postvars["auth_key"][0]
        except:
            logging.error("No method/auth")
            self.result(ERROR_BAD_REQUEST)
            return

        try:
            params = json.loads(postvars["params"][0])
        except:
            params = {}

        methods = self.server.service.methods


        if method in ["auth", "login"]: # AUTH is deprecated
            self._do_headers("application/octet-stream", 200)
            response, data = self.sessions.login(auth_key, params)
            self.push_response(response, data)


        elif method == "logout":
            self._do_headers("application/octet-stream", 200)
            response, data = self.sessions.logout(auth_key)
            self.push_response(response, data)


        elif method in methods:

            user = self.sessions[auth_key]
            if not user:
                self.result(403, "Not authorised")
                return

            self._do_headers("application/octet-stream", 200)
            try:
                for response, data in methods[method](user, params):
                    self.push_response(response, data)
                    if response >= 300:
                        logging.error("{} failed to {}: {}".format(user, method, data))
            except:
                msg = log_traceback("{} failed to {}:".format(user, method))
                self.push_response(400, "\n{}\n".format(msg))
        else:
            logging.error("{} is not implemented".format(method))
            self.result(ERROR_NOT_IMPLEMENTED, False)
            return

    def push_response(self, response, data):
        data = json.dumps([response, data])
        self._echo("{}\n".format(data))



class HiveHTTPServer(HTTPServer):
    pass


class Service(BaseService):
    def on_init(self):
        self.methods = {}

        for module in [hive_assets, hive_system, hive_items, hive_dramatica]:
            for method in dir(module):
                if not method.startswith("hive_"):
                    continue
                method_title = method[5:]
                module_name  = module.__name__.split(".")[-1]
                exec ("self.methods['{}'] = {}.{}".format(method_title, module_name, method ))
                logging.debug("Enabling method '{}'".format(method_title))

        try:
            port = int(self.config.find("port").text)
        except:
            port = 42000

        logging.debug("Starting hive at port {}".format(port))

        self.server = HiveHTTPServer(('',port), HiveHandler)

        self.sessions = Sessions()
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())


    def on_main(self):
        db = DB()
        db.query("SELECT id_service, state, last_seen FROM nx_services")
        service_status = db.fetchall()
        messaging.send("hive_heartbeat", service_status=service_status)
