import cgi
import thread
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from nx import *
from nx.services import BaseService

from .sessions import Sessions
from .sessions import Sessions

import hive_assets
import hive_system
import hive_items
import hive_dramatica

reload(sys)
sys.setdefaultencoding('utf-8')


class HiveHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        pass

    def _do_headers(self,mime="application/json",response=200,headers=[]):
        self.send_response(response)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
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

    def do_GET(self):
        pass

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

        elif method == "ping":
            self._do_headers("text/txt", 200)
            self.push_response(200, "pong")


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
