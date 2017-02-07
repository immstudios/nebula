import cgi

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class ControlHandler(BaseHTTPRequestHandler):
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
        self.wfile.write(istring.encode("utf-8"))

    def result(self, r):
        response, data = r
        self._do_headers(response=response)
        self._echo(json.dumps([response, data]))


    def error(self,response):
        self._do_headers(response=response)

    def do_GET(self):
        service = self.server.service
        self.result(service.cg_list(id_channel=1))

    def do_POST(self):
        service = self.server.service
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            logging.debug("No post data")
            self.error(400)
            return

        try:
            method = postvars["method"][0]
            params = json.loads(postvars["params"][0])
        except:
            logging.debug("Malformed request")
            self.error(400)
            return

        methods = {
            "take" : service.take,
            "cue" : service.cue,
            "freeze" : service.freeze,
            "retake" : service.retake,
            "abort" : service.abort,
            "stat" : service.stat,
            "cg_list" : service.cg_list,
            "cg_exec" : service.cg_exec,
            "recover" : service.channel_recovery
            }

        if not method in methods:
            self.error(501)
            return

        self.result(methods[method](**params))



