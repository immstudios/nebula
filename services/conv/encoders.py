from nx import *
from nx.objects import Asset, asset_by_path
from nx.core.metadata import meta_types

import uuid
import stat
import subprocess
import thread

class Encoder():
    def __init__(self, asset, task, vars):
        self.asset = asset
        self.task = task
        self.vars = vars
        self.proc = None

    def configure(self):
        pass

    def run(self):
        pass

    def is_working(self):
        return False

    def get_progress(self):
        """Should return float between 0.0 and 1.0"""
        return 0

    def finalize(self):
        pass



def temp_file(id_storage, ext):
    if id_storage:
        temp_path = os.path.join(storages[id_storage].local_path,".nx", "creating")
    else:
        temp_path = "/tmp/nx"

    if not os.path.exists(temp_path):
        try:
            os.makedirs(temp_path)
        except:
            return False

    temp_name = str(uuid.uuid1()) + ext
    return os.path.join(temp_path, temp_name)


## ENCODERS COMMON
#########################################################################
## FFMPEG

def interleave(fname):
    opath = os.getcwd()
    os.chdir(os.path.dirname(fname))
    args = ["MP4Box", "-inter", "500"]
    args.append(fname)
    p = subprocess.Popen(args)
    while p.poll() == None:
        time.sleep(.1)
    os.chdir(opath)
    return True

class Ffmpeg(Encoder):
    def configure(self):
        self.ffparams = ["ffmpeg", "-y"]
        self.ffparams.extend(["-i", self.asset.get_file_path()])
        asset = self.asset

        id_storage = int(self.task.find("storage").text)
        self.id_storage = id_storage
        self.target_rel_path = eval(self.task.find("path").text)
        temp_ext  = os.path.splitext(self.target_rel_path)[1]

        for p in self.task:
            if p.tag == "param":
                value = str(eval(p.text)) if p.text else ""
                if p.attrib["name"] == "ss":
                    self.ffparams.insert(2, "-ss")
                    self.ffparams.insert(3, value)
                else:
                    self.ffparams.append("-{}".format(p.attrib["name"]))
                    if value:
                        self.ffparams.append(value)

            elif p.tag == "pre":
                exec(p.text)

            elif p.tag == "paramset" and eval(p.attrib["condition"]):
                for pp in p.findall("param"):
                    value = str(eval(pp.text)) if pp.text else ""
                    self.ffparams.append("-{}".format(pp.attrib["name"]))
                    if value:
                        self.ffparams.append(value)

        ########################
        ## Output path madness

        if not storages[id_storage]:
            return "Target storage is not mounted"

        self.temp_file_path   = temp_file(id_storage, temp_ext)
        if not self.temp_file_path:
            return "Unable to create temp directory"

        self.target_file_path = os.path.join(storages[id_storage].local_path, self.target_rel_path)
        self.target_dir_path  = os.path.split(self.target_file_path)[0]

        if not (os.path.exists(self.target_dir_path) and stat.S_ISDIR(os.stat(self.target_dir_path)[stat.ST_MODE])):
            try:
                os.makedirs(self.target_dir_path)
            except:
                return "Unable to create output directory"

        ## Output path madness
        ########################

        self.ffparams.append(self.temp_file_path)
        return False # no error



    def run(self):
        logging.debug("Executing {}".format(str(self.ffparams)))
        self.progress = 0
        self.proc = subprocess.Popen(self.ffparams, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    def is_working(self):
        if not self.proc or self.proc.poll() == None:
            return True
        return False


    def get_progress(self):
        if not self.proc:
            return 0, "Starting"

        if self.proc.poll() == 0:
            return COMPLETED, "Encoding completed"
        elif self.proc.poll() > 0:
            print (self.proc.stderr.read())
            return FAILED, "Encoding failed"
        else:
            try:
                ln = self.proc.stderr.readline().split(" ")
            except:
                pass
            else:
                for k in ln:
                    if k.startswith("time="):
                        try:
                            PZ = self.asset["duration"]
                            hh, mm, ss = k.replace("time=","").split(":")
                            PC = (int(hh)*3600) + (int(mm)*60) + float(ss)
                            self.progress = PC / PZ
                            return self.progress, "Encoding media"
                        except:
                            pass
            return self.progress, "Encoding media"


    def finalize(self):
        new = None
        asset = Asset(self.asset.id) # Reload asset (possibly changed during encoding)

        if self.task.find("target").text == "new":
            id_storage = self.id_storage
            r = asset_by_path(id_storage, self.target_rel_path)
            if r:
                new = Asset(r)
                logging.info("Updating asset {!r}".format(new))
                keys = new.meta.keys()
                for key in keys:
                    if key in meta_types and meta_types[key].namespace in ["qc", "fmt"]:
                        new[key] = ""
            else:
                logging.info("Creating new asset for {!r} conversion.".format(asset))
                new = Asset()
                new["media_type"]   = FILE
                new["content_type"] = VIDEO

                new["version_of"]   = asset.id
                new["id_storage"]   = id_storage
                new["path"]         = self.target_rel_path
                new["origin"]       = "Video conversion"
                new["id_folder"]    = asset["id_folder"]

                for key in asset.meta:
                    if key in meta_types and meta_types[key].namespace in ["AIEB", "m"]:
                        new[key] = asset[key]

            new["status"] = CREATING



        for intra in self.task.findall("intra"):
            exec(intra.text)

        try:
            os.rename(self.temp_file_path, self.target_file_path)
        except:
            return "Unable to move output file to target destination"

        if new is not None:
            new.save()

        for post in self.task.findall("post"):
            exec(post.text)

        if new is not None:
            new.save()
        asset.save()

## FFMPEG
#########################################################################
## FTP

from ftplib import FTP

class Ftp(Encoder):
    def configure(self):
        asset = self.asset

        source_storage = int(self.task.find("source_storage").text)
        source_path = eval(self.task.find("source_path").text)
        self.target_path = eval(self.task.find("path").text)

        self.host = self.task.find("host").text
        self.login = self.task.find("login").text
        self.password = self.task.find("password").text

        self._fpath = os.path.join(storages[source_storage].local_path, source_path)
        self._fsize    = os.path.getsize(self._fpath)
        self._file     = open(self._fpath, 'rb')
        self._fwritten = 0
        self.ret_code  = 0
        self.ret_msg   = ""


    def run(self):
        self._is_working = True
        logging.debug("Connecting to ftp://{}".format(self.host))
        self.ftp = FTP(self.host)
        self.ftp.login(self.login, self.password)
        logging.debug("Uploading")
        thread.start_new_thread(self.upload, ())


    def update_progress(self, b):
        self._fwritten += 1024

    def upload(self):
        self._is_working = True
        try:
            self.ftp.storbinary('STOR {}'.format(self.target_path), self._file, 1024, self.update_progress)
        except:
            self.ret_code = FAILED
            self.ret_msg = str(sys.exc_info())
        self._is_working = False

    def is_working(self):
        return self._is_working

    def get_progress(self):
        progress = self._fwritten / float(self._fsize)
        return self.ret_code or progress, self.ret_msg or "Uploading"

    def finalize(self):
        self.ftp.quit()
        self._file.close()
