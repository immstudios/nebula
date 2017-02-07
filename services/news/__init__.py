import thread

from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from nx import *
from nx.services import BaseService
from nx.objects import *

from rss import *

class ControlHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        pass

    def _do_headers(self,mime="application/json", response=200, headers=[]):
        self.send_response(response)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        for h in headers:
            handler.send_header(h[0],h[1])
        self.send_header('Content-type', mime)
        self.end_headers()

    def _echo(self,istring):
        self.wfile.write(istring.encode("utf-8"))

    def result(self, data):
        self._do_headers()
        self._echo(json.dumps(data))

    def error(self,response):
        self._do_headers(response=response)

    def do_GET(self):
        service = self.server.service
        article = service.get_article(1, ["google_news"])
        if not article:
           self.result(False)
           return
        self.result(article.meta)



class Service(BaseService):
    def on_init(self):
        port = 42200
        self.max_articles = 20
        self.sources = []

        for source in self.settings.findall("source"):
            try:
                title = source.find("title").text
                mod = source.find("module").text
                url = source.find("url").text
            except:
                continue

            try:
                parser = source.find("parser").text
            except:
                parser = False

            self.sources.append([title, mod, url, parser])


        if not self.sources:
            self.sources = [
                    ["google_news", "rss", "https://news.google.com/news?cf=all&hl=cs&pz=1&ned=cs_cz&topic=h&output=rss", google_news_parser]
                ]

        self.history = {}
        self.server = HTTPServer(('', port), ControlHandler)
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())


    def get_article(self, channel, groups):
        db = DB()
        db.query("""SELECT id_object FROM nx_assets WHERE id_folder = 6 AND origin='News' AND mtime > {}
            AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='news_group' AND value IN ({}))
            AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='qc/state' AND value='4')
            """.format(time.time() - 86400,   ", ".join(["'{}'".format(group) for group in groups])))

        articles = [r[0] for r in db.fetchall()]
        if not articles:
            return False

        if channel not in self.history:
            self.history[channel] = {}

        id_asset = sorted(articles, key=lambda id_asset: self.history[channel].get(id_asset, 0))[0]

        self.history[channel][id_asset] = time.time()

        article = Asset(id_asset)
        return article





    def get_free_asset(self, db=False):
        if not db:
            db=DB()

        db.query("SELECT COUNT(id_object) from nx_assets WHERE id_folder=6 AND origin='News'")
        count = db.fetchall()[0][0]
        if count < self.max_articles:
            return Asset(db=db)

        db.query("SELECT id_object FROM nx_assets WHERE id_folder=6 and origin='News' ORDER BY mtime ASC LIMIT 1")
        return Asset(db.fetchall()[0][0], db=db)



    def push_item(self, item, db=False):
        db = db or DB()
        db.query("SELECT id_object FROM nx_meta WHERE tag='identifier/guid' AND value = %s AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='news_group' AND value=%s )",
                [item["identifier/guid"], item["news_group"] ]
            )

        if db.fetchall():
            return
        try:
            logging.debug("Saving news item {}".format(item["title"]))
        except:
            logging.debug("Saving news item")

        asset = self.get_free_asset(db=db)
        asset.meta = {}
        asset["id_folder"] = 6
        asset["origin"] = "News"
        asset["status"] = ONLINE
        asset["ctime"] = time.time()
        asset["qc/state"] = 4
        asset["media_type"] = VIRTUAL
        asset["content_type"] = TEXT
        asset.meta.update(item)
        asset.save()


    def on_main(self):
        db = DB()
        for group, mod, source, parser in self.sources:
            if mod == "rss":
                feed = RSS(source, parser=parser)
                for item in feed.items:
                    item["news_group"] = group
                    self.push_item(item, db=db)

