import thread


from nebula import *

from .plugins import *
from .controller import *
from .caspar import Caspar

class Service(BaseService):
    def on_init(self):
        allowed_channels = []
        chlist = self.settings.find("channels")
        if chlist is not None:
            for ch in chlist.findall("channel"):
                allowed_channels.append(int(ch.text))

        self.caspar = Caspar()
        for id_channel in config["playout_channels"]:
            if allowed_channels and id_channel not in allowed_channels:
                continue

            channel_cfg = config["playout_channels"][id_channel]
            logging.debug("Initializing playout channel {}: {}".format(id_channel, channel_cfg["title"]))

            channel = self.caspar.add_channel(channel_cfg["caspar_host"],
                                              channel_cfg["caspar_port"],
                                              channel_cfg["caspar_channel"],
                                              channel_cfg["feed_layer"],
                                              id_channel
                                             )

            channel.playout_spec  = channel_cfg["playout_spec"]
            channel.fps           = channel_cfg.get("fps", 25.0)
            channel.on_main       = self.channel_main
            channel.on_change     = self.channel_change
            channel.on_recovery   = self.channel_recovery

            channel.cued_asset    = False
            channel.current_asset = False
            channel.current_event = False
            channel._changed      = False
            channel._last_run     = False
            channel._next_studio  = False
            channel._now_studio   = False
            channel.enabled_plugins = channel_cfg.get("plugins", [])
            channel.plugins         = PlayoutPlugins(channel)

        if not config["playout_channels"]:
            logging.error("No playout channel configured")
            self.shutdown(no_restart=True)

        try:
            port = int(self.settings.find("port").text)
        except:
            port = 42100

        self.server = HTTPServer(('',port), ControlHandler)
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())



    def cue(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        id_item    = kwargs.get("id_item", False)
        db         = kwargs.get("db", DB())
        lcache     = kwargs.get("cache", cache)

        if not (id_item and id_channel):
            return 400, "Bad request"

        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"

        channel = self.caspar[id_channel]
        channel.cued_asset = False


        item  = Item(id_item, db=db, cache=lcache)
        if not item:
            return 404, "No such item"

        if item["item_role"] == "studio":
            logging.info("Next is studio item")
            fname = "BLANK"
            kwargs["auto"] = True #False
            channel._next_studio = item.id
            return channel.cue(fname, **kwargs)

        if not item["id_asset"]:
            return 400, "Cannot cue virtual item"

        id_playout = item.asset[channel.playout_spec]
        playout_asset = Asset(id_playout, db=db, cache=lcache)

        if not os.path.exists(playout_asset.file_path):
            return 404, "Playout asset is offline"

        kwargs["mark_in"] = item["mark_in"]
        kwargs["mark_out"] = item["mark_out"]

        if item["run_mode"] == 1:
            kwargs["auto"] = False
        else:
            kwargs["auto"] = True

        channel._next_studio = False
        fname = os.path.splitext(os.path.basename(playout_asset["path"]))[0].encode("utf-8")
        return channel.cue(fname, **kwargs)


    def take(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        res = channel.take()
        return res


    def freeze(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        return channel.freeze()


    def retake(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        return channel.retake()


    def abort(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        return channel.abort()


    def stat(self, **kwargs):
        return "200", "stat"


    def cg_list(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]

        result = []

        for j, plugin in enumerate(channel.plugins):
            if not plugin.slots:
                continue

            p = {
                "id" : j,
                "title" : plugin.title,
                "slots":[]
                }

            for i, slot in enumerate(plugin.slots):
                s = {
                    "slot_type" : slot.slot_type,
                    "id" : i
                    }

                for op in slot.ops:
                    if op == "title":
                        s["title"] = slot["title"]
                    elif op == "source":
                        s["data"] = slot["source"]()
                    elif op == "value":
                        s["value"] = slot["value"]

                p["slots"].append(s)

            result.append(p)
        return 200, result


    def cg_exec(self, **kwargs):
        id_channel = kwargs.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]

        plugin = channel.plugins[kwargs["id_plugin"]]
        slot = plugin.slots[kwargs["id_slot"]]

        if slot.slot_type == "button":
            slot["action"]()

        if slot.slot_type in ["select", "text"]:
            slot["value"] = kwargs["value"]

        return 200, "OK"


    def channel_main(self, channel):
        if not channel.cued_asset and channel.cued_item:
            channel.cued_asset = Item(channel.cued_item).asset

        data = {}
        data["id_channel"]    = channel.ident
        data["current_item"]  = channel.current_item
        data["cued_item"]     = channel.cued_item
        data["position"]      = channel.get_position()
        data["duration"]      = channel.get_duration()
        data["current_title"] = channel.current_asset["title"] if channel.current_asset else "(no clip)"
        data["cued_title"]    = channel.cued_asset["title"]    if channel.cued_asset    else "(no clip)"
        data["request_time"]  = channel.request_time
        data["paused"]        = channel.paused
        data["stopped"]       = channel.stopped
        data["id_event"]      = channel.current_event.id if channel.current_event else False

        data["current_fname"] = channel.current_fname
        data["cued_fname"]    = channel.cued_fname

        messaging.send("playout_status", **data)

        for plugin in channel.plugins:
            try:
                plugin.main()
            except:
                log_traceback("Playout plugin error:")

        if channel.current_item and not channel.cued_item and not channel._cueing:  # and not channel._next_studio and not channel._now_studio:
            self.cue_next(channel)

        if channel.stopped and channel._next_studio and channel._next_studio == channel.cued_item:
            self.on_studio_enter(channel)


    def channel_change(self, channel):
        if not channel.current_item:
            return

        db = DB()
        item = Item(channel.current_item, db=db)
        if item["item_role"] == "studio":
            channel.current_asset = Asset(meta=item.meta)
        else:
            channel.current_asset = item.asset
        channel.current_event = item.event
        channel.cued_asset = False

        logging.info ("Advanced to {}".format(item))

        if channel._last_run:
            db.query("UPDATE nx_asrun SET stop = %s WHERE id_run = %s",  [int(time.time()) , channel._last_run])

        if channel.current_asset:
            db.query("INSERT INTO nx_asrun (id_channel, start, stop, title, id_item, id_asset) VALUES (%s,%s,%s,%s,%s,%s) ",
                [
                channel.ident,
                int(time.time()),
                0,
                db.sanit(channel.current_asset["title"]),
                channel.current_item,
                channel.current_asset.id
                ])
            channel._last_run = db.lastid()
            db.commit()

        else:
            channel._last_run = False


        for plugin in channel.plugins:
            try:
                plugin.on_change()
            except:
                log_traceback("Plugin on_change error")



    def channel_recovery(self, channel):
        logging.warning("Performing recovery")
        logging.debug("Restarting Caspar")
        channel.server.query("RESTART")
        time.sleep(5)
        while not success(channel.server.connect()[0]):
            time.sleep(1)
        logging.debug("Connection estabilished. recovering playback")
        time.sleep(5)

        db = DB()
        db.query("SELECT id_item, start FROM nx_asrun WHERE id_channel = %s ORDER BY id_run DESC LIMIT 1", (channel.ident,))
        try:
            last_id_item, last_start = db.fetchall()[0]
        except IndexError:
            logging.error("Unable to perform recovery. Last item information is not available")
        last_item = Item(last_id_item, db=db)

        if last_start + last_item.duration <= time.time():
            logging.info("Last {} has been broadcasted. starting next item".format(last_item))
            new_item = self.cue_next(channel, id_item=last_item.id, db=db, play=True)
        else:
            logging.info("Last {} has not been fully broadcasted. starting next item anyway.... FIX ME".format(last_item))
            new_item = self.cue_next(channel, id_item=last_item.id, db=db, play=True)

        if not new_item:
            logging.error("Recovery failed. Unable to cue")
            channel.cue("BLANK", id_item=False, play=True)
            channel.cue("BLANK", id_item=False)
            return

        channel.current_item = new_item.id
        channel.cued_item = False
        channel.cued_fname = False

        self.channel_change(channel)


    def cue_next(self, channel, id_item=False, db=False, level=0, play=False):
        channel._cueing = True
        db = db or DB()
        lcache = Cache()
        id_item = id_item or channel.current_item
        item_next = get_next_item(id_item, db=db, cache=lcache)


        if item_next["run_mode"] == 1:
            auto = False
        else:
            auto = True


        logging.info("Auto-cueing {}".format(item_next))
        stat, res = self.cue(id_item=item_next.id, id_channel=channel.ident, play=play, cache=lcache, auto=auto)


        if failed(stat):
            if level > 5:
                logging.error("Cue it yourself....")
                return None
            logging.warning("Unable to cue {} ({}). Trying next one.".format(item_next, res))
            item_next = self.cue_next(channel, id_item=item_next.id, db=db, level=level+1, play=play)
        return item_next


    def on_studio_enter(self, channel):
        logging.goodnews("STUDIO ENTER")
        channel._now_studio = channel._next_studio
        channel._next_studio = False


    def on_studio_leave(self, channel):
        logging.goodnews("STUDIO LEAVE")
        channel._next_studio = False
        channel._now_studio = False


    def on_main(self):
        """
        This method checks if the following event should start automatically at given time.
        It does not handle AUTO playlist advancing and default auto-cueing etc
        """
        local_cache = Cache()
        db = DB()
        for id_channel in self.caspar.channels:
            if self.caspar.channels[id_channel]._changing:
                continue

            id_item = self.caspar.channels[id_channel].current_item # YES. CURRENT
            if not id_item:
                continue

            # TODO: use channel.current_event
            current_event = get_item_event(id_item, db=db, cache=local_cache)

            if not current_event:
                logging.warning("Unable to fetch current event")
                continue

            db.query("""SELECT e.id_object FROM nx_events AS e WHERE e.id_channel = {} AND e.start > {} AND e.start <= {} ORDER BY e.start DESC LIMIT 1""".format(
                    id_channel,
                    current_event["start"],
                    time.time()
                    ))
            try:
                next_event_id = db.fetchall()[0][0]
            except:
                continue

            next_event = Event(next_event_id, db=db, cache=local_cache)
            run_mode = int(next_event["run_mode"]) or RUN_AUTO

            if not run_mode:
                continue

            elif not next_event.bin.items:
                continue

            elif run_mode == RUN_MANUAL:
                pass # ?????

            elif run_mode == RUN_SOFT:
                logging.info("Soft cue {}".format(next_event))

                for i,r in enumerate(current_event.bin.items):
                    if r["item_role"] == "lead_out":
                        try:
                            self.cue(id_channel=id_channel, id_item=current_event.bin.items[i+1].id, db=db, cache=local_cache)
                            break
                        except IndexError:
                            pass
                    else:
                        id_item = next_event.bin.items[0].id
                        if id_item != self.caspar.channels[id_channel].cued_item:
                            self.cue(id_channel=id_channel, id_item=id_item, db=db, cache=local_cache)

            elif run_mode == RUN_HARD:
                id_item = next_event.bin.items[0].id
                self.cue(id_channel=id_channel, id_item=id_item, play=True, db=db, cache=local_cache)
