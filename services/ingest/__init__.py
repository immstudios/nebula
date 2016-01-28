from nx import *
from nx.services import BaseService
from nx.objects import Asset, Event

ACTION_PRIMARY_INGEST = -1
ACTION_BACKUP_INGEST  = -2



class CaptureTask():
    def __init__(self, event, **kwargs):
        self.event = event
        self.asset = Asset(event["id_magic"])
        self.ingest_mode = "BACKUP"

    @property
    def id_event(self):
        if self.event:
            return self.event.id
        else:
            return 0

    def __repr__(self):
        return ""



class Capture():
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.settings = kwargs
        self.id_job = False

        self.task = None
        self.proc = None

    def __call__(self, task):
        if self.capturing:
            if task and self.task.id == task.id:
                self.update_status()
            else:
               self.stop()
        elif task:
            self.task = task
            self.start()

        print "Ingest status: ", self.capturing


    @property
    def state(self):
        if self.settings["ingest_mode"] == "PRIMARY":
            return ACTION_PRIMARY_INGEST
        else:
            return ACTION_BACKUP_INGEST

    @property
    def capturing(self):
        if not self.proc:
            return False
        return self.proc.poll() == None


    def update_status(self):
        print ("Ingesting", self.task)
        return
        pz = stop - start
        pc = now - start
        progress = int((float(pc)/float(pz))*100)



    def start(self):
        logging.info("Starting ingest {}".format(self.task))
        return
        db = DB()

        # TODO: Create job record

        if self.current_event.ingest_mode == "PRIMARY":
            fname = self.current_asset.file_path
        else:
            backup_fname = strftime("%Y_%m_%d_%H%M%S",localtime(time())) + os.path.splitext(self.current_asset["PATH"])[1]
            fname = os.path.join(self.cache_dir,backup_fname)

        cmd = "../bmdcapture -C %s -m %s -I %s -c 8 -F nut -f pipe:1 | " % (self.bmddevice,self.bmdmode,self.bmdinput)
        cmd+= "ffmpeg -y -i - "
        fmt = self.service.config.find("format")
        for param in fmt.findall("param"):
         cmd+= "-%s %s " % (param.attrib["name"],param.text)
        cmd+= "'%s'" % fname

        self.proxy_name = False
        if self.current_event.ingest_mode == "PRIMARY":
         try:  fmt = self.service.config.find("proxy")
         except: pass # proxy nechcem
         else:

          try: os.makedirs(ProxyPath(self.current_event.id_asset))
          except: pass

          if os.path.exists(ProxyPath(self.current_event.id_asset)):
           cmd += " "
           for param in fmt.findall("param"):
            cmd+= "-%s %s " % (param.attrib["name"],param.text)
           self.proxy_name = ProxyFile(self.current_event.id_asset)
           cmd += "'%s'" % self.proxy_name

         osvcdr = os.getcwd()
         os.chdir(self.service.svcdir)
         self.proc = subprocess.Popen(cmd, shell=True)#,stderr=subprocess.PIPE)
         os.chdir(osvcdr)


    def stop(self):
        if self.capturing:
            pass

        self.id_job = False
        self.proc = None
        self.task = None





class Service(BaseService):
    def on_init(self):
        self.id_channel = int(self.settings.find("channel").text)
        self.current_task = None

        self.capture = Capture(self)
        """
                self,
                ingest_mode = self.settings.find("ingest_mode").text, # PRIMARY - Nahrava se do assetu, BACKUP - Nahrava se lokalne
                cache_dir   = self.settings.find("cache_dir").text,
                bmd_device  = self.settings.find("device").text,
                bmd_mode    = self.settings.find("mode").text,
                bmd_input   = self.settings.find("input").text
            )
        """


        # DEMO EVENT
        db = DB()
        e = Event(5529, db=db)
        e["start"] = time.time() + 3
        e["stop"] = time.time() + 30
        e.save()


    def on_main(self):
        now = int(time.time())

        db = DB()
        db.query("SELECT id_object, start, stop, id_magic FROM nx_events WHERE id_channel = %s AND start < %s AND stop > %s ORDER BY start LIMIT 1", (self.id_channel, now, now ))
        for id_event, start, stop, id_asset in db.fetchall():
            event = Event(id_event, db=db)

            if not self.current_task:
                task = CaptureTask(event)
                self.current_task = task
                break

            elif self.current_task.id_event != id_event:
                logging.warning("Another event should be ingested right now....")
                continue
            break
        else:
            self.current_task = None

        self.capture(self.current_task)

