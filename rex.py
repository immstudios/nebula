import os
import sys
import subprocess
import time
import json
import traceback

# do not import anything
__all__ = []

DEBUG, INFO, WARNING, ERROR, GOOD_NEWS = range(5)
PLATFORM = "windows" if sys.platform == "win32" else "unix"

def indent(src, l=4):
    return "\n".join(["{}{}".format(l*" ", s.rstrip()) for s in src.split("\n")])

class Logging():
    def __init__(self, user="REX"):
        self.user = user
        self.handlers = []
        self.formats = {
            INFO      : "INFO       {0:<15} {1}",
            DEBUG     : "\033[34mDEBUG      {0:<15} {1}\033[0m",
            WARNING   : "\033[33mWARNING\033[0m    {0:<15} {1}",
            ERROR     : "\033[31mERROR\033[0m      {0:<15} {1}",
            GOOD_NEWS : "\033[32mGOOD NEWS\033[0m  {0:<15} {1}"
            }

        self.formats_win = {
            DEBUG     : "DEBUG      {0:<10} {1}",
            INFO      : "INFO       {0:<10} {1}",
            WARNING   : "WARNING    {0:<10} {1}",
            ERROR     : "ERROR      {0:<10} {1}",
            GOOD_NEWS : "GOOD NEWS  {0:<10} {1}"
            }

    def add_handler(self, handler):
        self.handlers.append(handler)

    def _send(self, msgtype, *args, **kwargs):
        message = " ".join([str(arg) for arg in args])
        user = kwargs.get("user", self.user)
        if kwargs.get("handlers", True):
            for handler in self.handlers:
                handler(user=self.user, message_type=msgtype, message=message)
        if PLATFORM == "unix":
            try:
                print (self.formats[msgtype].format(user, message))
            except:
                print (message.encode("utf-8"))
        else:
            try:
                print (self.formats_win[msgtype].format(user, message))
            except:
                print (message.encode("utf-8"))

    def debug(self, *args, **kwargs):
        self._send(DEBUG, *args, **kwargs)

    def info(self, *args, **kwargs):
        self._send(INFO, *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._send(WARNING, *args, **kwargs)

    def error(self, *args, **kwargs):
        self._send(ERROR, *args, **kwargs)

    def goodnews(self, *args, **kwargs):
        self._send(GOOD_NEWS, *args, **kwargs)

logging = Logging()

def log_traceback(message="Exception!", **kwargs):
    tb = traceback.format_exc()
    msg = "{}\n\n{}".format(message, indent(tb))
    logging.error(msg, **kwargs)
    return msg


def critical_error(msg, **kwargs):
    logging.error(msg, **kwargs)
    logging.debug("Critical error. Terminating program.")
    sys.exit(1)





class Repository():
    def __init__(self, parent,  url, **kwargs):
        self.parent = parent
        self.url = url
        self.settings = kwargs
        self.base_name = os.path.basename(url)
        self.path = os.path.join(self.parent.vendor_dir, self.base_name)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def __getitem__(self, key):
        return self.settings[key]




class Rex(object):
    def __init__(self):
        self.app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.vendor_dir =os.path.join(self.app_dir, "vendor")
        self.manifest_path = os.path.join(self.app_dir, "rex.json")
        self.self_update()
        self.main()

    @property
    def force_update(self):
        return "--rex-update" in sys.argv

    def chdir(self, path):
        os.chdir(path)

    @property
    def repos(self):
        if not hasattr(self, "_repos"):
            if not os.path.exists(self.manifest_path):
                self._repos = []
            try:
                self.manifest = json.load(open(self.manifest_path))
                if not self.manifest:
                    return []
                self._repos = []
                for repo_url in self.manifest.keys():
                    repo_settings = self.manifest[repo_url]
                    repo = Repository(self, repo_url, **repo_settings)
                    self._repos.append(repo)
            except Exception:
                log_traceback()
                critical_error("Unable to load rex manifest. Exiting")
                self._repos = []
        return self._repos

    def self_update(self):
        if not self.force_update:
            return
        #if not os.path.exists(".rex_devel"):
        #    logging.debug("This is a development machine. Skipping rex auto update.")
        #    return
        import urllib2
        response = urllib2.urlopen("https://imm.cz/rex.py")
        new_rex = response.read()
        old_rex = open("rex.py").read()
        if new_rex != old_rex:
            logging.info("Updating REX")
        else:
            logging.info("REX is up to date")


    def main(self):
        for repo in self.repos:
            try:
                self.update(repo) and self.post_install(repo)
            except Exception:
                log_traceback()
        self.chdir(self.app_dir)

    def update(self, repo):
        if not os.path.exists(self.vendor_dir):
            os.makedirs(self.vendor_dir)

        if os.path.exists(repo.path):
            if self.force_update:
                self.chdir(repo.path)
                cmd = ["git", "pull"]
            else:
                return True
        else:
            self.chdir(self.vendor_dir)
            cmd = ["git", "clone", repo.url]

        p = subprocess.Popen(cmd)
        while p.poll() == None:
            time.sleep(.1)
        print ("ret_code", p.returncode)

        return True

    def post_install(self, repo):
        if repo.get("python-path") and not repo.path in sys.path:
            sys.path.insert(0, repo.path)



rex = Rex()

