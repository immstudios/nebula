from nx import *

import thread
import telnetlib

def basefname(fname):
    """Platform dependent path splitter (caspar is always on win)"""
    return os.path.splitext(fname.split("\\")[-1])[0]


class CasparChannel():
    def __init__(self, server, channel):
        self.server  = server  # CasparServer class instance
        self.channel = channel # Caspar channel (that "X" integer in PLAY x-y command)
        self.fps = 25.0        # default

        self.xstat  = "<channel>init</channel>"
        self.chdata = {}
        self.plugins = []

        self.current_item   = False
        self.current_fname  = False
        self.cued_item      = False
        self.cued_fname     = False
        self.paused         = False
        self.stopped        = False

        self._cueing        = False
        self._changing      = False
        self.request_time = self.recovery_time = time.time()

        self.pos = self.dur = self.fpos = self.fdur = 0
        self.cued_in = self.cued_out = self.current_in = self.current_out = 0


    def on_main(self, channel=False):
        pass

    def on_change(self, channel=False):
        pass

    def on_recovery(self, channel=False):
        pass

    def get_position(self):
        return int(self.fpos - (self.current_in * self.fps))

    def get_duration(self):
        dur = self.fdur
        if self.current_out > 0: dur -= dur - (self.current_out*self.fps)
        if self.current_in  > 0: dur -= (self.current_in*self.fps)
        return dur


    def cue(self, fname, **kwargs):
        self._cueing    = True

        id_item    = kwargs.get("id_item", fname)
        auto       = kwargs.get("auto", True)
        play       = kwargs.get("play", False)
        mark_in    = kwargs.get("mark_in",0)
        mark_out   = kwargs.get("mark_out",0)
        layer      = kwargs.get("layer", self.feed_layer)

        marks = ""
        if mark_in:  marks += " SEEK %d"   % (float(mark_in)*self.fps)
        if mark_out: marks += " LENGTH %d" % ((float(mark_out) - float(mark_in))*self.fps)

        if play:# or self.stopped:
            q = "PLAY %s-%d %s %s"     % (self.channel,layer,fname,marks)
        else:
            q = "LOADBG %s-%d %s %s %s" % (self.channel,layer,fname,["","AUTO"][auto],marks)

        stat, res = self.server.query(q)

        if failed(stat):
            res = "Unable to cue \"{}\" {} - args: {}".format(fname, res, str(kwargs))
            logging.error(res)
            self.cued_item  = False
            self.cued_fname = False
            self._cueing    = False
        else:
            self.cued_item  = id_item
            self.cued_fname = fname
            self.cued_in    = mark_in
            self.cued_out   = mark_out
            self._cueing    = True
            res = "Cued item {} ({})".format(self.cued_item, fname)
            logging.debug(res)

        return (stat, res)


    def clear(self,layer=False):
        layer = layer or self.feed_layer
        return self.server.query("CLEAR {}-{}".format(self.channel, layer))


    def take(self,layer=False):
        layer = layer or self.feed_layer
        if not self.cued_item:
            return 400, "Unable to take. No item is cued."
        self.paused = False
        return self.server.query("PLAY {}-{}".format(self.channel, layer))


    def retake(self,layer=False):
        layer = layer or self.feed_layer
        seekparam = "%s" % (int(self.current_in*self.fps))
        if self.current_out: seekparam += " LENGTH %s" % (int((self.current_out-self.current_in)*self.fps))
        q = "PLAY %d-%d %s SEEK %s"%(self.channel, layer, self.current_fname,  seekparam)
        self.paused = False
        return self.server.query(q)


    def freeze(self,layer=False):
        layer = layer or self.feed_layer

        if not self.paused:
            q = "PAUSE %d-%d"%(self.channel,layer)
            msg = "Playback paused"
        else:
            if self.current_out:
                LEN = "LENGTH %s" %int((self.current_out-self.current_in)*self.fps)
            else:
                LEN = ""

            q = "PLAY %d-%d %s SEEK %s %s"%(self.channel, layer, self.current_fname, self.fpos, LEN)
            msg = "Playback resumed"

        stat, res = self.server.query(q)
        if success(stat):
            self.paused = not self.paused

        return stat, msg


    def abort(self, layer=False):
        layer = layer or self.feed_layer
        if not self.cued_item:
            return 400, "Unable to abort. No item is cued."
        q = "LOAD {}-{} {}".format(self.channel, layer, self.cued_fname)
        if self.cued_in:
            q += " SEEK {}".format(int(self.cued_in * self.fps))
        if self.cued_out:
            q += " LENGTH {}".format(int((self.cued_out-self.cued_in) * self.fps))
        return self.server.query(q)


    def update_stat(self):
        stat, res = self.server.query("INFO {}".format(self.channel))
        if failed(stat):
            return False
        try:
            xstat = ET.XML(res)
        except:
            return False
        else:
            self.request_time = time.time()
            self.xstat = xstat
            return True


    def main(self):
        #######################################
        ## Get main video_layer

        try:
           for layer in self.xstat.find("stage").find("layers").findall("layer"):
              if int(layer.find("index").text) != self.feed_layer:
                  continue
              else:
                  video_layer = layer
                  break
           else:
             raise Exception
        except:
            self.on_main(self) # cg channels need this
            return # Unable to find video feed layer

        ## Get video_layer
        #######################################
        ## Get cued_fname

        try:
            if video_layer.find("status").text == "paused":
                self.paused = True
                self.stopped = False
            elif video_layer.find("status").text == "stopped" or int(video_layer.find("frames-left").text) <= 0:
                self.stopped = True
                self.paused = False
            elif video_layer.find("status").text == "playing":
                self.paused = False
                self.stopped = False

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
            log_traceback()
            current_fname = False


        ## Get current_fname
        #######################################
        ## Get cued_fname

        try:
            bg_prod = video_layer.find("background").find("producer").find("destination").find("producer")
            if bg_prod.find("type").text == "image-producer":
                cued_fname = basefname(bg_prod.find("location").text)
            elif bg_prod.find("type").text == "empty-producer":
                cued_fname = False # No video is cued
            else:
                cued_fname = basefname(bg_prod.find("filename").text)
        except:
            cued_fname = False

        ## Get cued_fname
        #######################################
        ## Auto recovery

        if not current_fname and time.time() - self.recovery_time > 10:
            self.on_recovery(self)
            return
        self.recovery_time = time.time()

        ## Auto recovery
        #######################################
        ## Playlist advancing


        if not cued_fname and current_fname and not self._cueing:
            self._changing = True
            changed = False
            if current_fname == self.cued_fname:
                self.current_item  = self.cued_item
                self.current_fname = self.cued_fname
                self.current_in    = self.cued_in
                self.current_out   = self.cued_out
                self.cued_in = self.cued_out = 0
                changed = True

            self.cued_fname = False
            self.cued_item  = False

            if changed:
                self.on_change(self)

            self._changing = False

        elif self.cued_item and cued_fname and cued_fname != self.cued_fname and not self._cueing:
            logging.warning ("Cue mismatch: This is not the file which should be cued. IS: %s vs. SHOULDBE: %s" % (cued_fname, self.cued_fname))
            self.cued_item = False # AutoCue in on_main should handle it next iteration


        self.on_main(self)
        self.current_fname = current_fname
        self._cueing = False


## Channel stuff... tricky
########################################################################
## Easy... should work



def server_ident(host, port):
    return "{}:{}".format(host, port)

class CasparServer():
    def __init__(self, host="localhost", port=5250):
        self.host = host
        self.port = port
        self.ident = server_ident(host, port)
        self.cmd_conn = self.inf_conn = False
        self.connect()

    def __repr__(self):
        return self.ident

    def connect(self):
        logging.debug("Connecting to CasparCG server at {}:{}".format(self.host, self.port))
        try:
            self.cmd_conn = telnetlib.Telnet(self.host, self.port)
            self.inf_conn = telnetlib.Telnet(self.host, self.port)
        except:
            return 503, "Connection failed"
        else:
            return 200, "OK"

    def query(self, q):
        if not (self.inf_conn and self.cmd_conn):
            return 500, "CasparCG server is offline"

        if q.startswith("INFO"):
            conn = self.inf_conn
        else:
            logging.debug("Executing AMCP: {}".format(q))
            conn = self.cmd_conn

        try:
            conn.write("%s\r\n"%q)
            result = conn.read_until("\r\n").strip()
        except:
            return 500, "Query execution failed"

        if not result:
            return 500, "No result"

        try:
            if result[0:3] == "202":
                return (202, result)

            elif result[0:3] in ["201","200"]:
                stat = int(result[0:3])
                result = conn.read_until("\r\n").strip()
                return stat, result

            elif int(result[0:1]) > 3:
                return int(result[0:3]), result
        except:
            return 500, "Malformed result"
        return 500, "Very strange result"


class Caspar():
    def __init__(self):
      self.servers  = {}
      self.channels = {}
      self.bad_requests  = {}
      thread.start_new_thread(self._start,())

    def add_channel(self, host, port, channel, feed_layer, ident):
      """
      Appends an output channel.
      Arguments:
      host, port : connection to running CasparCG server
      channel    : CASPAR's channel id (First number in "PLAY 1-1" command....)
      feed_layer : "main" caspar layer - that one with playlist.
      ident      : YOUR unique identification of the channel (aka nx_channels.id_channel)
      """
      server = self._add_server(host, port)
      self.channels[ident] = CasparChannel(self.servers[server], channel)
      self.channels[ident].ident = ident
      self.channels[ident].feed_layer = feed_layer
      return self.channels[ident]

    def _add_server(self, host, port):
        server = server_ident(host,port)
        if not server in self.servers:
            self.servers[server] = CasparServer(host, port)
        return server

    def _start(self):
        while True:
            self._main()
            time.sleep(.2)

    def _main(self):
        idents = self.channels.keys()
        for ident in idents:
            channel = self.channels[ident]
            if not channel.update_stat():
                logging.warning("Channel {} update stat failed".format(ident))
                if not ident in self.bad_requests:
                    self.bad_requests[ident] = 0
                self.bad_requests[ident] += 1
                if self.bad_requests.get(ident, 0) > 10:
                    logging.error("Connection lost. Reconnecting...")
                    if success(channel.server.connect()[0]):
                        logging.goodnews("Connection estabilished")
                    else:
                        logging.error("Connection call failed")
                        time.sleep(2)
                time.sleep(.1)
                continue
            else:
                self.bad_requests[ident] = 0
                channel.main()




    def __getitem__(self, id_channel):
        return self.channels[id_channel]

