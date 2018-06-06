try:
    import _thread as thread
except ImportError:
    import thread

from nebula import *

from .request_handler import *
from .caspar_controller import *



class Service(BaseService):
    def on_init(self):
        if not config["playout_channels"]:
            logging.error("No playout channel configured")
            self.shutdown(no_restart=True)

        self.last_run = False

        try:
            self.id_channel = int(self.settings.find("id_channel").text)
        except Exception:
            self.id_channel = int(min(config["playout_channels"].keys()))

        self.channel_config = config["playout_channels"][self.id_channel]

        self.caspar_host         = self.channel_config.get("caspar_host", "localhost")
        self.caspar_port         = int(self.channel_config.get("caspar_port", 5250))
        self.caspar_channel      = int(self.channel_config.get("caspar_channel", 1))
        self.caspar_feed_layer   = int(self.channel_config.get("caspar_feed_layer", 10))
        self.fps                 = float(self.channel_config.get("fps", 25.0))

        self.current_live = False
        self.cued_live = False

        self.controller = CasparController(self)

        try:
            port = int(self.settings.find("port").text)
        except:
            port = 42100

        self.server = HTTPServer(('', port), PlayoutRequestHandler)
        self.server.service = self
        self.server.methods = {
                "take" : self.take,
                "cue" : self.cue,
                "freeze" : self.freeze,
                "retake" : self.retake,
                "abort" : self.abort,
                "stat" : self.stat,
                "plugin_list" : self.plugin_list,
                "plugin_exec" : self.plugin_exec,
                "recover" : self.channel_recover
            }
        thread.start_new_thread(self.server.serve_forever,())




    def cue(self, **kwargs):
        db         = kwargs.get("db", DB())
        lcache     = kwargs.get("cache", cache)

        if "item" in kwargs and isinstance(kwargs["item"], Item):
            item = kwargs["item"]
            del(kwargs["item"])
        elif "id_item" in kwargs:
            item = Item(int(kwargs["id_item"]), db=db, cache=lcache)
            item.asset
            del(kwargs["id_item"])
        else:
            return NebulaResponse(400, "Unable to cue. No item specified")

        if not item:
            return NebulaResponse(404, "Unable to cue. Item ID: {} does not exist".format(id_item))

        if item["item_role"] == "live":
            logging.info("Next is item is live")
            fname = self.channel_config.get("live_source", "BLANK")
            self.cued_live = item
            return self.controller.cue(fname, item, **kwargs)

        if not item["id_asset"]:
            return NebulaResponse(400, "Unable to cue virtual item ID: {}".format(id_item))

        asset = item.asset
        playout_path = asset.get_playout_full_path(self.id_channel)

        if not os.path.exists(playout_path):
            return NebulaResponse(404, "Unable to cue. Playout path {} does not exist".format(playout_path))

        kwargs["mark_in"] = item["mark_in"]
        kwargs["mark_out"] = item["mark_out"]

        if item["run_mode"] == 1:
            kwargs["auto"] = False
        else:
            kwargs["auto"] = True

        self.cued_live = False
        return self.controller.cue(asset.get_playout_name(self.id_channel), item,  **kwargs)





    def cue_next(self, **kwargs):
        item = kwargs.get("item", self.controller.current_item)
        level = kwargs.get("level", 0)
        db = kwargs.get("db", DB())
        play = kwargs.get("play", False)
        lcache = kwargs.get("cache", Cache())

        if not item:
            logging.warning("Unable to cue next item. No current clip")
            return

        self.controller.cueing = True
        item_next = get_next_item(item.id, db=db, cache=lcache)


        if item_next["run_mode"] == 1:
            auto = False
        else:
            auto = True

        logging.info("Auto-cueing {}".format(item_next))
        result = self.cue(item=item_next, play=play, cache=lcache, auto=auto)


        if result.is_error:
            if level > 5:
                logging.error("Cue it yourself....")
                return False
            logging.warning("Unable to cue {} ({}). Trying next one.".format(item_next, result.message))
            item_next = self.cue_next(item=item_next, db=db, level=level+1, play=play)
        return item_next


    def take(self, **kwargs):
        return self.controller.take(**kwargs)

    def freeze(self, **kwargs):
        return self.controller.freeze(**kwargs)

    def retake(self, **kwargs):
        return self.controller.retake(**kwargs)

    def abort(self, **kwargs):
        return self.controller.abort(**kwargs)

    def stat(self, **kwargs):
        #TODO
        return "200", "stat"


    def plugin_list(self, **kwargs):
        return NebulaResponse(501, "Not implemented")
        #TODO
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


    def plugin_exec(self, **kwargs):
        return NebulaResponse(501, "Not implemented")
        #TODO

        plugin = channel.plugins[kwargs["id_plugin"]]
        slot = plugin.slots[kwargs["id_slot"]]

        if slot.slot_type == "button":
            slot["action"]()

        if slot.slot_type in ["select", "text"]:
            slot["value"] = kwargs["value"]

        return 200, "OK"


    def on_progress(self):
        data = {}
        data["id_channel"]    = self.id_channel
        data["current_item"]  = self.controller.current_item.id if self.controller.current_item else False
        data["cued_item"]     = self.controller.cued_item.id if self.controller.cued_item else False
        data["position"]      = self.controller.position
        data["duration"]      = self.controller.duration
        data["current_title"] = self.controller.current_item["title"] if self.controller.current_item else "(no clip)"
        data["cued_title"]    = self.controller.cued_item["title"]    if self.controller.cued_item    else "(no clip)"
        data["request_time"]  = self.controller.request_time
        data["paused"]        = self.controller.paused
        data["stopped"]       = self.controller.stopped
#        data["id_event"]      = self.controller.current_event.id if channel.current_event else False

        data["current_fname"] = self.controller.current_fname
        data["cued_fname"]    = self.controller.cued_fname

        messaging.send("playout_status", **data)

#        for plugin in channel.plugins:
#            try:
#                plugin.main()
#            except:
#                log_traceback("Playout plugin error:")

#        if self.controller.current_item and (not self.controller.cued_item) and (not self.controller.cueing):  # and not channel._next_studio and not channel._now_studio:
#            self.cue_next()

#        if channel.stopped and channel._next_studio and channel._next_studio == channel.cued_item:
#            self.on_studio_enter(channel)


    def on_change(self):
        return
        #TODO
        if not self.controller.current_item:
            return


        return
        db = DB()
        if item["item_role"] == "studio":
            channel.current_asset = Asset(meta=item.meta)
        else:
            channel.current_asset = item.asset
        channel.current_event = item.event
        channel.cued_asset = False

        logging.info ("Advanced to {}".format(item))

#        if channel._last_run:
#            db.query("UPDATE nx_asrun SET stop = %s WHERE id_run = %s",  [int(time.time()) , channel._last_run])
#
#        if channel.current_asset:
#            db.query("INSERT INTO nx_asrun (id_channel, start, stop, title, id_item, id_asset) VALUES (%s,%s,%s,%s,%s,%s) ",
#                [
#                channel.ident,
#                int(time.time()),
#                0,
#                db.sanit(channel.current_asset["title"]),
#                channel.current_item,
#                channel.current_asset.id
#                ])
#            channel._last_run = db.lastid()
#            db.commit()
#
#        else:
#            channel._last_run = False

#        for plugin in channel.plugins:
#            try:
#                plugin.on_change()
#            except:
#                log_traceback("Plugin on_change error")



    def channel_recover(self, channel):
        #TODO
        logging.warning("Performing recovery")
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
        last_item.asset

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


    def on_live_enter(self):
        logging.goodnews("LIVE ENTER")
        self.current_live = True
        self.cued_live = False


    def on_live_leave(self):
        logging.goodnews("LIVE LEAVE")
        self.current_live = False

    def on_main(self):
        """
        This method checks if the following event
        should start automatically at given time.
        It does not handle AUTO playlist advancing
        """

        #if self.controller.changing:
        #    return

        current_item = self.controller.current_item # YES. CURRENT
        if not current_item:
            return

        local_cache = Cache()
        db = DB()

        current_event = get_item_event(current_item.id, db=db, cache=local_cache)

        if not current_event:
            logging.warning("Unable to fetch current event")
            return


        db.query(
                "SELECT meta FROM events WHERE id_channel = %s AND start > %s AND start <= %s ORDER BY start DESC LIMIT 1",
                [self.id_channel, current_event["start"], time.time()]
            )

        try:
            next_event = Event(meta=db.fetchall()[0][0], db=db, cache=local_cache)
        except IndexError:
            return

        run_mode = int(next_event["run_mode"]) or RUN_AUTO

        if not run_mode:
            return

        elif not next_event.bin.items:
            return

        elif run_mode == RUN_MANUAL:
            pass # ?????

        elif run_mode == RUN_SOFT:
            logging.info("Soft cue {}".format(next_event))

            for i, r in enumerate(current_event.bin.items):
                if r["item_role"] == "lead_out":
                    try:
                        self.cue(
                                id_channel=id_channel,
                                id_item=current_event.bin.items[i+1].id,
                                db=db,
                                cache=local_cache
                            )
                        break
                    except IndexError:
                        pass
            else:
                id_item = next_event.bin.items[0].id
                if id_item != self.controller.next_item.id:
                    self.cue(
                            id_channel=id_channel,
                            id_item=id_item,
                            db=db,
                            cache=local_cache
                        )

        elif run_mode == RUN_HARD:
            id_item = next_event.bin.items[0].id
            self.cue(
                    id_channel=id_channel,
                    id_item=id_item,
                    play=True,
                    db=db,
                    cache=local_cache
                )
