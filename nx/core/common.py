import os
import sys
import json
import time

import hashlib
import socket

from xml.etree import ElementTree as ET

from nxtools import *
from .constants import *


if PLATFORM == "windows":
    python_cmd = "c:\\python27\python.exe"
    def ismount(path):
        return True
else:
    python_cmd = "python"
    from posixpath import ismount

#
# Config
#

class Config(dict):
    def __init__(self):
        super(Config, self).__init__()
        self["site_name"] = "Unnamed"
        self["user"] = "Nebula"              # Service identifier. Should be overwritten by service/script.
        self["host"] = socket.gethostname()  # Machine hostname

        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            local_settings_path = sys.argv[1]
        else:
            local_settings_path = "settings.json"

        settings_files = [
                    "/etc/nebula.json",
                    local_settings_path
                ]
        settings = {}
        for settings_file in settings_files:
            if os.path.exists(settings_file):
                try:
                    settings.update(json.load(open(settings_file)))
                    logging.debug("Parsing {}".format(settings_file), handlers=False)
                except Exception:
                    log_traceback(handlers=False)

        if not settings:
            critical_error("Unable to open site settings")
        self.update(settings)

config = Config()

#
# Utilities
#

def success(ret_code):
    return ret_code < 400

def failed(ret_code):
    return not success(ret_code)

def get_hash(string):
    string = string + config.get("hash_salt", "")
    return hashlib.sha256(string).hexdigest()

def xml(text):
    return ET.XML(text)

#
# Messaging
#

class Messaging():
    def __init__(self):
        self.configured = False

    def configure(self):
        self.addr = config.get("seismic_addr", "224.168.2.8")
        self.port = int(config.get("seismic_port", 42112))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        self.configured = True

    def send(self, method, **data):
        if not self.configured:
            return
        try:
            self.sock.sendto(
                encode_if_py3(
                    json.dumps([
                        time.time(),
                        config["site_name"],
                        config["host"],
                        method,
                        data
                        ])
                    ),
                (self.addr, self.port)
                )
        except Exception:
            log_traceback(handlers=False)

messaging = Messaging()

#
# Logging
#

def seismic_log(**kwargs):
    messaging.send("log", **kwargs)

logging.user = config["user"]
logging.add_handler(seismic_log)

#
# Filesystem
#

class Storage(object):
    def __init__(self, id,  **kwargs):
        self.id = id
        self.settings = kwargs

    def __getitem__(self, key):
        return self.settings[key]

    def __repr__(self):
        return "storage ID:{} ({})".format(self.id, self["title"])

    @property
    def local_path(self):
        if self["protocol"] == "local":
            return self["path"]
        elif PLATFORM == "unix":
            return os.path.join("/mnt/{}_{:02d}".format(config["site_name"], self.id))
        #elif PLATFORM == "windows":
            #TODO
        logging.warning("Unsuported {} protocol '{}' on this platform.".format(self, self["protocol"]))

    def __len__(self):
        if self["protocol"] == "local" and os.path.isdir(self["path"]):
            return True
        return ismount(self.local_path) and len(os.listdir(self.local_path)) != 0


class Storages(object):
    def __getitem__(self, key):
        #TODO error_handling
        return Storage(key, **config["storages"][key])

    def __iter__(self):
        return config["storages"].__iter__()

storages = Storages()
