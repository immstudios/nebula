import imp
import thread

from nx import *
from nx.objects import *
from nx.plugins import plugin_path

from dramatica.common import DramaticaCache, DramaticaAsset
from dramatica.scheduling import DramaticaBlock, DramaticaRundown
from dramatica.templates import DramaticaTemplate
from dramatica.timeutils import *
from dramatica.solving import solvers


NX_TAGS = [
    (str, "title"),
    (str, "title/subtitle"),
    (str, "title/series"),
    (str, "series/season"),
    (str, "series/episode"),
    (str, "description"),
    (str, "genre"),
    (str, "format"),
    (str, "rights"),
    (str, "source"),
    (str, "identifier/vimeo"),
    (str, "identifier/youtube"),
    (str, "identifier/main"),
    (str, "role/performer"),
    (str, "role/director"),
    (str, "role/composer"),
    (str, "album"),
    (str, "path"),
    (int, "id_storage"),
    (int, "qc/state"),
    (int, "id_folder"),
    (int, "promoted"),
    (int, "contains/nudity"),
    (int, "contains/violence"),
    (int, "ctime"),
    (int, "mtime"),
    (float, "duration"),
    (float, "mark_in"),
    (float, "mark_out"),
    (float, "audio/bpm"),
    ]


def day_start(ts, start):
    hh, mm = start
    r =  ts - (hh*3600 + mm*60)
    dt = datetime.datetime.fromtimestamp(r).replace(
        hour = hh,
        minute = mm,
        second = 0
        )
    return time.mktime(dt.timetuple())


def load_solvers():
    solvers_path = os.path.join (plugin_path, "dramatica_solvers")
    if not os.path.exists(solvers_path):
        logging.warning("Dramatica solvers directory not found. Only default solvers will be available")
        return
    for fname in os.listdir(solvers_path):
        if not fname.endswith(".py"):
            continue
        mod_name = os.path.splitext(fname)[0]
        py_mod = imp.load_source(mod_name, os.path.join(solvers_path,fname))
        manifest = py_mod.__manifest__
        solver_name = manifest["name"]
        logging.info("Loading dramatica solver {}".format(solver_name))
        solvers[solver_name] = py_mod.Solver

load_solvers()


def get_template(tpl_name):
    fname = os.path.join(plugin_path, "dramatica_templates", "{}.py".format(tpl_name))
    if not os.path.exists(fname):
        logging.error("Template does not exist")
        return
    py_mod = imp.load_source(tpl_name, fname)
    return py_mod.Template


def nx_assets_connector():
    local_cache = Cache()
    db = DB()
    db.query("SELECT id_object FROM nx_assets WHERE id_folder != 10 AND media_type = 0 AND content_type=1 AND status = 1 AND origin IN ('Production')")
    for id_object, in db.fetchall():
        asset = Asset(id_object, db=db, cache=local_cache)
        if asset["qc/state"] == 3:
            continue
        yield asset.meta

def nx_history_connector(now):
    local_cache = Cache()
    db = DB()

    start = now - (3600*24*90)
    stop = now + (3400*24*7)

    cond = ""
    cond += " AND start > {}".format(start)
    cond += " AND start < {}".format(stop)
    db.query("SELECT id_object FROM nx_events WHERE id_channel in ({}){} ORDER BY start ASC".format(", ".join([str(i) for i in config["playout_channels"] ]), cond ))

    for id_object, in db.fetchall():
        event = Event(id_object, db=db, cache=local_cache)
        tstamp = event["start"]
        if tstamp < now - (3600*24*30):
            if event["id_asset"]:
                yield (event["id_channel"], tstamp, event["id_asset"])
                continue

        for item in event.bin.items:
            yield (event["id_channel"], tstamp, item["id_asset"])
            tstamp += item.duration









class Session():
    def __init__(self):
        self.cache = False
        self.rundown = False
        self.start_time = self.end_time = self.id_channel = 0
        self.affected_events = []
        self.busy = False
        self.status = "Waiting"

    def open_rundown(self, id_channel=1, date=time.strftime("%Y-%m-%d")):
        if not self.busy:
            self.busy = True
            thread.start_new_thread(self._open_rundown, (id_channel, date ))
            while self.busy:
                time.sleep(.2)
                yield self.status

    def _open_rundown(self, id_channel=1, date=time.strftime("%Y-%m-%d")):
        day_start = config["playout_channels"][id_channel].get("day_start", (6,0))

        logging.debug("Loading asset cache")
        self.cache = DramaticaCache(NX_TAGS)
        for msg in self.cache.load_assets(nx_assets_connector()):
            self.status = msg

        self.id_channel = id_channel
        self.start_time = datestr2ts(date, *day_start)
        self.end_time = self.start_time + (3600*24)

        logging.debug("Loading history")
        stime = time.time()
        for msg in self.cache.load_history(nx_history_connector(self.start_time)):
            self.status = msg

        logging.debug("History items loaded in {} seconds".format(time.time()-stime))

        self.rundown = DramaticaRundown(
                self.cache,
                day=list(int(i) for i in date.split("-")),
                day_start=day_start,
                id_channel=id_channel
            )

        db = DB()
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start >= %s and start < %s ORDER BY start ASC", (id_channel, self.start_time, self.end_time))
        for id_event, in db.fetchall():
            event = Event(id_event, db=db)
            self.msg = "Loading {}".format(event)
            event.meta["id_event"] = event.id
            block = DramaticaBlock(self.rundown, **event.meta)
            block.config = json.loads(block["dramatica/config"] or "{}")

            for eitem in event.bin.items:

                imeta = { key : eitem[key] for key in eitem.meta if eitem[key] }
                imeta.update({
                    "id_item" : eitem.id,
                    "id_object" : eitem["id_asset"],
                    "is_optional" : eitem["is_optional"]
                    })

                if imeta["id_object"]:
                    item = self.cache[imeta["id_object"]]
                else:
                    item = DramaticaAsset()
                block.add(item, **imeta)

            self.rundown.add(block)

        self.busy = False



    def solve(self, id_event=False):
        if not self.busy:
            self.busy = True
            thread.start_new_thread(self._solve, (id_event,))
            while self.busy:
                time.sleep(.2)
                yield self.status

    def _solve(self, id_event=False):
        for msg in self.rundown.solve(id_event):
            self.status = msg
        self.busy = False


    def save(self, id_event=False):
        if not self.rundown:
            return
        db = DB()
        for block in self.rundown.blocks:

            if id_event and block["id_event"] and id_event != block["id_event"]:
                continue

            if block["id_event"]:
                event = Event(block["id_event"], db=db)
                ebin = event.bin
            else:
                event = Event(db=db)
                ebin = Bin(db=db)
                ebin.save()

            old_items = [item for item in ebin.items]
            ebin.items = []

            for pos, bitem in enumerate(block.items):
                try:
                    item = old_items.pop(0)
                    t_keys = [key for key in item.meta if key not in ["id_object", "position"]]
                except IndexError:
                    item = Item(db=db)
                    t_keys = []

                t_keys.extend(["mark_in", "mark_out", "item_role", "promoted", "is_optional"])
                if not bitem.id:
                    t_keys.append("title")
                    t_keys.append("duration")

                if item.id:
                    item.meta = {"id_object":item.id}
                else:
                    item.meta = {}

                for key in t_keys:
                    if bitem[key]:
                        item.meta[key] = bitem[key]

                item["ctime"] = item["mtime"] = time.time()
                item["id_bin"] = ebin.id
                item["id_asset"] = bitem.id
                item["position"] = pos+1


                yield "Saving {}".format(item)
                item.save()
                ebin.items.append(item)

            for item in old_items:
                logging.info("Removing remaining {}".format(item))
                yield "Removing {}".format(item)
                item.delete()

            for key in block.meta:
                if key in ["id_object", "id_event"]:
                    continue
                if block.meta[key]:
                    event[key] = block[key]

            ebin.save()
            event["id_magic"] = ebin.id
            event["id_channel"] = self.id_channel
            event["dramatica/config"] = json.dumps(block.config)
            event["start"] = block["start"]
            self.affected_events.append(event.id)
            yield "Saving {}".format(event)
            event.save()

    def clear_rundown(self, id_channel, date):
        day_start = config["playout_channels"][id_channel].get("day_start", (6,0))
        start_time = datestr2ts(date, *day_start)
        end_time = start_time + (3600*24)
        logging.info("Clear rundown {}".format(time.strftime("%Y-%m-%d", time.localtime(start_time))))

        db = DB()
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start >= %s and start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
        for id_event, in db.fetchall():
            id_event = int(id_event)
            event = Event(id_event, db=db)
            if not event:
                logging.warning("Unable to delete non existent event ID {}".format(id_event))
                continue

            for item in event.bin.items:
                if not item.id:
                    continue
                yield "Deleting {}".format(item)
                item.delete()
            event.bin.items = []
            event.bin.delete()
            self.affected_events.append(event.id)
            yield "Deleting {}".format(event)
            event.delete()



################################################################################################


def hive_dramatica(user, params={}):
    id_channel = params["id_channel"]
    date = params["date"]
    session = Session()
    if params.get("clear", False):
        for msg in session.clear_rundown(id_channel=id_channel, date=date):
            yield -1, {"message":msg}

    if params.get("template", False) or params.get("solve", False):
        for msg in session.open_rundown(id_channel=id_channel, date=date):
            yield -1, {"message":msg}

        if params.get("template", False):
            yield -1, {"message":"applying template"}
            template_class = get_template("default_template")
            template = template_class(session.rundown)
            template.apply()

        if params.get("solve", False):
            for msg in session.solve(id_event=params.get("id_event", False)):
                yield -1, {"message":msg}

        for msg in session.save(id_event=params.get("id_event", False)):
            yield -1, {"message":msg}

    if session.affected_events:
        messaging.send("objects_changed", sender=False, objects=session.affected_events, object_type="event", user="anonymous Firefly user")

    yield 200, "ok"
