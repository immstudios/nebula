__all__ = ["CasparController"]

import os
import time
import threading

from nxtools import logging, log_traceback
from nxtools.caspar import CasparCG

from nx.core.common import NebulaResponse
from nx.helpers import bin_refresh
from nx.objects import Item

from .caspar_data import CasparOSCServer


class CasparController(object):
    time_unit = "s"

    def __init__(self, parent):
        self.parent = parent

        self.caspar_host = parent.channel_config.get("caspar_host", "localhost")
        self.caspar_port = int(parent.channel_config.get("caspar_port", 5250))
        self.caspar_osc_port = int(parent.channel_config.get("caspar_osc_port", 5253))
        self.caspar_channel = int(parent.channel_config.get("caspar_channel", 1))
        self.caspar_feed_layer = int(parent.channel_config.get("caspar_feed_layer", 10))

        self.should_run = True

        self.current_item = Item()
        self.current_fname = False
        self.cued_item = False
        self.cued_fname = False
        self.cueing = False
        self.cueing_time = 0
        self.cueing_item = False
        self.stalled = False

        # To be updated based on CCG data
        self.channel_fps = self.fps
        self.paused = False
        self.loop = False
        self.pos = self.dur = 0

        if not self.connect():
            logging.error("Unable to connect CasparCG Server. Shutting down.")
            self.parent.shutdown()
            return

        self.caspar_data = CasparOSCServer(self.caspar_osc_port)
        self.lock = threading.Lock()
        self.work_thread = threading.Thread(target=self.work, args=())
        self.work_thread.start()

    def shutdown(self):
        logging.info("Controller shutdown requested")
        self.should_run = False
        self.caspar_data.shutdown()

    def on_main(self):
        if time.time() - self.caspar_data.last_osc > 5:
            logging.warning("Waiting for OSC")

    @property
    def id_channel(self):
        return self.parent.id_channel

    @property
    def request_time(self):
        return time.time()

    @property
    def fps(self):
        return self.parent.fps

    @property
    def position(self) -> float:
        """Time position (seconds) of the clip currently playing"""
        if self.current_item:
            return self.pos - self.current_item.mark_in()
        return self.pos

    @property
    def duration(self) -> float:
        """Duration (seconds) of the clip currently playing"""
        if self.parent.current_live:
            return 0
        return self.dur

    def connect(self):
        """Connect to a running CasparCG instance using AMCP protocol"""
        self.cmdc = CasparCG(self.caspar_host, self.caspar_port)
        return self.cmdc.connect()

    def query(self, *args, **kwargs) -> NebulaResponse:
        """Send an AMCP query to the CasparCG server"""
        return self.cmdc.query(*args, **kwargs)

    def work(self):
        while self.should_run:
            try:
                self.main()
            except Exception:
                log_traceback()
            time.sleep(1 / self.fps)
        logging.info("Controller work thread shutdown")

    def main(self):
        channel = self.caspar_data[self.caspar_channel]
        if not channel:
            return

        layer = channel[self.caspar_feed_layer]
        if not layer:
            return

        foreground = layer["foreground"]
        background = layer["background"]

        current_fname = os.path.splitext(foreground.name)[0]
        cued_fname = os.path.splitext(background.name)[0]
        pos = foreground.position
        dur = foreground.duration

        self.channel_fps = channel.fps
        self.paused = foreground.paused
        self.loop = foreground.loop

        #        if cued_fname and (not self.paused) and (pos == self.pos) and (not self.parent.current_live) and self.cued_item and (not self.cued_item["run_mode"]):
        #            if self.stalled and self.stalled < time.time() - 5:
        #                logging.warning("Stalled for a long time")
        #                logging.warning("Taking stalled clip (pos: {})".format(self.pos))
        #                self.take()
        #            elif not self.stalled:
        #                logging.debug("Playback is stalled")
        #                self.stalled = time.time()
        #        elif self.stalled:
        #            logging.debug("No longer stalled")
        #            self.stalled = False

        self.pos = pos
        self.dur = dur

        #
        # Playlist advancing
        #

        advanced = False
        if self.parent.cued_live:
            if (
                (background.producer == "empty")
                and (foreground.producer != "empty")
                and not self.cueing
            ):
                self.current_item = self.cued_item
                self.current_fname = "LIVE"
                advanced = True
                self.cued_item = False
                self.parent.on_live_enter()

        else:
            if (not cued_fname) and (current_fname):
                if current_fname == self.cued_fname:
                    self.current_item = self.cued_item
                    self.current_fname = self.cued_fname
                    advanced = True
                self.cued_item = False

        if advanced and not self.cueing:
            try:
                self.parent.on_change()
            except Exception:
                log_traceback("Playout on_change failed")

        if self.current_item and not self.cued_item and not self.cueing:
            self.cueing = True
            if not self.parent.cue_next():
                self.cueing = False

        if self.cueing:
            if cued_fname == self.cueing:
                logging.goodnews(f"Cued {self.cueing}")
                self.cued_item = self.cueing_item
                self.cueing_item = False
                self.cueing = False
            elif self.parent.cued_live:
                if background.producer != "empty":
                    logging.goodnews(f"Cued {self.cueing}")
                    self.cued_item = self.cueing_item
                    self.cueing_item = False
                    self.cueing = False

            else:
                logging.debug(f"Waiting for cue {self.cueing} (is {cued_fname})")
                if time.time() - self.cueing_time > 5 and self.current_item:
                    logging.warning("Cueing again")
                    self.cueing = False
                    self.parent.cue_next()

        elif (
            not self.cueing
            and self.cued_item
            and cued_fname
            and cued_fname != self.cued_fname
            and not self.parent.cued_live
        ):
            logging.error(f"Cue mismatch: IS: {cued_fname} SHOULDBE: {self.cued_fname}")
            self.cued_item = False

        self.current_fname = current_fname
        self.cued_fname = cued_fname

        try:
            self.parent.on_progress()
        except Exception:
            log_traceback("Playout on_progress failed")

    def cue(self, fname, item, layer=None, play=False, auto=True, loop=False, **kwargs):
        layer = layer or self.caspar_feed_layer

        query_list = ["PLAY" if play else "LOADBG"]
        query_list.append(f"{self.caspar_channel}-{layer}")
        query_list.append(fname)

        if auto:
            query_list.append("AUTO")
        if loop:
            query_list.append("LOOP")
        if item.mark_in():
            query_list.append(f"SEEK {int(item.mark_in() * self.channel_fps)}")
        if item.mark_out():
            query_list.append(f"LENGTH {int(item.duration * self.channel_fps)}")

        query = " ".join(query_list)

        self.cueing = fname
        self.cueing_item = item
        self.cueing_time = time.time()

        result = self.query(query)

        if result.is_error:
            message = f'Unable to cue "{fname}" {result.data}'
            self.cued_item = Item()
            self.cued_fname = False
            self.cueing = False
            self.cueing_item = False
            self.cueing_time = 0
            return NebulaResponse(result.response, message)
        if play:
            self.cueing = False
            self.cueing_item = False
            self.cueing_time = 0
            self.current_item = item
            self.current_fname = fname
        return NebulaResponse(200)

    def clear(self, layer=None):
        layer = layer or self.caspar_feed_layer
        result = self.query(f"CLEAR {self.channel}-{layer}")
        return NebulaResponse(result.response, result.data)

    def take(self, **kwargs):
        layer = kwargs.get("layer", self.caspar_feed_layer)
        if not self.cued_item or self.cueing:
            return NebulaResponse(400, "Unable to take. No item is cued.")
        result = self.query(f"PLAY {self.caspar_channel}-{layer}")
        if result.is_success:
            if self.parent.current_live:
                self.parent.on_live_leave()
            message = "Take OK"
            self.stalled = False
        else:
            message = "Take failed: {result.data}"
        return NebulaResponse(result.response, message)

    def retake(self, **kwargs):
        layer = kwargs.get("layer", self.caspar_feed_layer)
        if self.parent.current_live:
            return NebulaResponse(409, "Unable to retake live item")
        seekparams = "SEEK " + str(int(self.current_item.mark_in() * self.channel_fps))
        if self.current_item.mark_out():
            seekparams += " LENGTH " + str(
                int(
                    (self.current_item.mark_out() - self.current_item.mark_in())
                    * self.channel_fps
                )
            )
        query = f"PLAY {self.caspar_channel}-{layer} {self.current_fname} {seekparams}"
        result = self.query(query)
        if result.is_success:
            message = "Retake OK"
            self.stalled = False
            self.parent.cue_next()
        else:
            message = "Take command failed: " + result.data
        return NebulaResponse(result.response, message)

    def freeze(self, **kwargs):
        layer = kwargs.get("layer", self.caspar_feed_layer)
        if self.parent.current_live:
            return NebulaResponse(409, "Unable to freeze live item")
        if self.paused:
            query = f"RESUME {self.caspar_channel}-{layer}"
            message = "Playback resumed"
        else:
            query = f"PAUSE {self.caspar_channel}-{layer}"
            message = "Playback paused"
        result = self.query(query)
        return NebulaResponse(result.response, message)

    def abort(self, **kwargs):
        layer = kwargs.get("layer", self.caspar_feed_layer)
        if not self.cued_item:
            return NebulaResponse(400, "Unable to abort. No item is cued.")
        query = f"LOAD {self.caspar_channel}-{layer} {self.cued_fname}"
        if self.cued_item.mark_in():
            seek = int(self.cued_item.mark_in() * self.channel_fps)
            query += f" SEEK {seek}"
        if self.cued_item.mark_out():
            length = int(
                (self.cued_item.mark_out() - self.cued_item.mark_in())
                * self.channel_fps
            )
            query += f" LENGTH {length}"
        result = self.query(query)
        return NebulaResponse(result.response, result.data)

    def set(self, key, value):
        if key == "loop":
            do_loop = int(str(value) in ["1", "True", "true"])
            result = self.query(
                f"CALL {self.caspar_channel}-{self.caspar_feed_layer} LOOP {do_loop}"
            )
            if self.current_item and bool(self.current_item["loop"] != bool(do_loop)):
                self.current_item["loop"] = bool(do_loop)
                self.current_item.save(notify=False)
                bin_refresh([self.current_item["id_bin"]], db=self.current_item.db)
            return NebulaResponse(result.response, f"SET LOOP: {result.data}")
        else:
            return NebulaResponse(400)
