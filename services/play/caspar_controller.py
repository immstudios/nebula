__all__ = ["CasparController"]

import os
import time
import telnetlib

try:
    import _thread as thread
except ImportError:
    import thread


from nx import *
from nxtools.caspar import CasparCG

def basefname(fname):
    """Platform dependent path splitter (caspar is always on win)"""
    return os.path.splitext(fname.split("\\")[-1])[0]


class CasparController(object):
    def __init__(self, parent):
        self.parent = parent

        self.current_item = False
        self.current_fname = False
        self.cued_item = False
        self.cued_fname = False
        self.cueing = False

        self.paused   = False
        self.stopped  = False

        self.pos = self.dur = self.fpos = self.fdur = 0
        self.cued_in = self.cued_out = self.current_in = self.current_out = 0

        self.bad_requests = 0
        self.request_time = self.recovery_time = time.time()

        self.connect()
        thread.start_new_thread(self.work, ())

    @property
    def id_channel(self):
        return self.parent.id_channel

    @property
    def host(self):
        return self.parent.caspar_host

    @property
    def port(self):
        return self.parent.caspar_port

    def connect(self):
        if not hasattr(self, "cmdc"):
            self.cmdc = CasparCG(self.host, self.port)
            self.infc = CasparCG(self.host, self.port)
            return True
        return self.cmdc.connect() and self.infc.connect()

    def query(self, *args, **kwargs):
        return self.cmdc.query(*args, **kwargs)

    def update_stat(self):
        result = self.infc.query(
                "INFO {}-{}".format(
                    self.parent.caspar_channel,
                    self.parent.caspar_feed_layer
                )
            )
        if result.is_error:
            return False
        try:
            xstat = xml(result.data)
        except Exception:
            log_traceback()
            return False
        else:
            self.request_time = time.time()
            self.xstat = xstat
            return True

    @property
    def fps(self):
        return self.parent.fps

    @property
    def position(self):
        return int(self.fpos - (self.current_in * self.fps))

    @property
    def duration(self):
        dur = self.fdur
        if self.current_out > 0:
            dur -= dur - (self.current_out*self.fps)
        if self.current_in > 0:
            dur -= (self.current_in*self.fps)
        return dur

    def work(self):
        while True:
            try:
                self.main()
            except Exception:
                log_traceback()
            time.sleep(.1)

    def main(self):
        if not self.update_stat():
            logging.warning("Channel {} update stat failed".format(self.id_channel))
            self.bad_requests += 1
            if self.bad_requests > 10:
                logging.error("Connection lost. Reconnecting...")
                if self.connect():
                    logging.goodnews("Connection estabilished")
                else:
                    logging.error("Connection call failed")
                    time.sleep(2)
            time.sleep(.3)
            return
        self.bad_requests = 0
        if not self.xstat:
            return False
        video_layer = self.xstat

        #
        # Current clip
        #

        try:
            fg_prod = video_layer.find("foreground").find("producer")
            if fg_prod.find("type").text == "image-producer":
                self.fpos = self.fdur = self.pos = self.dur = 0
                current_fname = basefname(fg_prod.find("location").text)
            elif fg_prod.find("type").text == "empty-producer":
                current_fname = False # No video is playing right now
            else:
                self.fpos = int(fg_prod.find("file-frame-number").text)
                self.fdur = int(fg_prod.find("file-nb-frames").text)
                self.pos  = int(fg_prod.find("frame-number").text)
                self.dur  = int(fg_prod.find("nb-frames").text)
                current_fname = basefname(fg_prod.find("filename").text)
        except:
            current_fname = False

        #
        # Next clip
        #

        try:
            bg_prod = video_layer.find("background").find("producer")
            if bg_prod.find("type").text == "image-producer":
                cued_fname = basefname(bg_prod.find("location").text)
            elif bg_prod.find("type").text == "empty-producer":
                cued_fname = False # No video is cued
            else:
                cued_fname = basefname(bg_prod.find("filename").text)
        except:
            cued_fname = False

        #
        # Auto recovery
        #

#        if not current_fname and time.time() - self.recovery_time > 10:
#            self.parent.channel_recover()
#            return
#        self.recovery_time = time.time()

        #
        # Playlist advancing
        #

        advanced = False

        if (not cued_fname) and (current_fname):
            if current_fname == self.cued_fname:
                self.current_item  = self.cued_item
                self.current_fname = self.cued_fname
                self.current_in    = self.cued_in
                self.current_out   = self.cued_out
                self.cued_in = self.cued_out = 0
                advanced = True

            self.cued_item = False


        if advanced:
            self.parent.on_change()
            self.parent.cue_next()




        if self.cued_item and cued_fname and cued_fname != self.cued_fname and not self.cueing:
            logging.warning("Cue mismatch: IS: {} SHOULDBE: {}".format(cued_fname, self.cued_fname))
            self.cued_item = False

        if self.current_item and not self.cued_item and not self.cueing:
            self.parent.cue_next()

        self.parent.on_progress()
        self.current_fname = current_fname
        self.cued_fname = cued_fname


    def cue(self, fname, item, **kwargs):
        auto       = kwargs.get("auto", True)
        layer      = kwargs.get("layer", self.parent.caspar_feed_layer)
        play       = kwargs.get("play", False)
        mark_in    = item.mark_in()
        mark_out   = item.mark_out()

        marks = ""
        if mark_in:
            marks += " SEEK {}".format(float(mark_in) * self.fps)
        if mark_out:
            marks += " LENGTH {}".format(int((float(mark_out) - float(mark_in)) * self.fps))

        if play:
            q = "PLAY {}-{} {}{}".format(
                    self.parent.caspar_channel,
                    layer,
                    fname,
                    marks
                )
        else:
            q = "LOADBG {}-{} {} {} {}".format(
                    self.parent.caspar_channel,
                    layer,
                    fname,
                    ["","AUTO"][auto],
                    marks
                )

        result = self.query(q)

        if result.is_error:
            message = "Unable to cue \"{}\" {} - args: {}".format(fname, result.data, str(kwargs))
            self.cued_item  = Item()
            self.cued_fname = False
        else:
            self.cued_item  = item
            self.cued_fname = fname
            self.cued_in    = mark_in
            self.cued_out   = mark_out
            message = "Cued item {} ({})".format(self.cued_item, fname)
        return NebulaResponse(result.response, message)


    def clear(self, **kwargs):
        layer = layer or self.parent.caspar_feed_layer
        result = self.query("CLEAR {}-{}".format(self.channel, layer))
        return NebulaResponse(result.response, result.data)

    def take(self, **kwargs):
        layer = kwargs.get("layer", self.parent.caspar_feed_layer)
        if not self.cued_item:
            return NebulaResponse(400, "Unable to take. No item is cued.")
        self.paused = False
        result = self.query("PLAY {}-{}".format(self.parent.caspar_channel, layer))
        if result.is_success:
            message = "Take OK"
        else:
            message = "Take command failed: " + result.data
        return NebulaResponse(result.response, message)

    def retake(self, **kwargs):
        layer = kwargs.get("layer", self.parent.caspar_feed_layer)
        seekparam = str(int(self.current_item.mark_in() * self.fps))
        if self.current_item.mark_out():
            seekparam += " LENGTH {}".format(int((self.current_item.mark_out() - self.current_item.mark_in()) * self.fps))
        q = "PLAY {}-{} {} SEEK {}".format(self.parent.caspar_channel, layer, self.current_fname, seekparam)
        self.paused = False
        result = self.query(q)
        if result.is_success:
            message = "Take OK"
        else:
            message = "Take command failed: " + result.data
        return NebulaResponse(result.response, message)

    def freeze(self, **kwargs):
        layer = kwargs.get("layer", self.parent.caspar_feed_layer)
        if not self.paused:
            q = "PAUSE {}-{}".format(self.parent.caspar_channel, layer)
            message = "Playback paused"
        else:
            q = "RESUME {}-{}".format(self.parent.caspar_channel, layer)
            message = "Playback resumed"
        result = self.query(q)
        if result.is_success:
            self.paused = not self.paused
        else:
            message = result.data
        return NebulaResponse(result.response, message)

    def abort(self, **kwargs):
        layer = kwargs.get("layer", self.parent.caspar_feed_layer)
        if not self.cued_item:
            return NebulaResponse(400, "Unable to abort. No item is cued.")
        q = "LOAD {}-{} {}".format(self.parent.caspar_channel, layer, self.cued_fname)
        if self.cued_item.mark_in():
            q += " SEEK {}".format(int(self.cued_item.mark_in() * self.fps))
        if self.cued_item.mark_out():
            q += " LENGTH {}".format(int((self.cued_item.mark_out() - self.cued_item.mark_in()) * self.fps))
        result =  self.query(q)
        if result.is_success:
            self.paused = True
        return NebulaResponse(result.response, result.data)