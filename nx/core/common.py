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

##
# Utilities
##

def success(ret_code):
    return ret_code < 400

def failed(ret_code):
    return not success(ret_code)

def get_hash(string):
    return hashlib.sha256(string).hexdigest()

def xml(text):
    return ET.XML(text)

##
# Config
##

class Config(dict):
    def __init__(self):
        super(Config, self).__init__()
        self["site_name"] = "Unnamed"
        self["user"] = "Nebula"              # Service identifier. Should be overwritten by service/script.
        self["host"] = socket.gethostname()  # Machine hostname
        try:
            local_settings = json.loads(open("local_settings.json").read())
        except:
            critical_error("Unable to open site_settings file.")
        self.update(local_settings)

config = Config()

##
# Messaging
##

class Messaging():
    def __init__(self):
        self.configure()

    def configure(self):
        self.addr = config.get("seismic_addr", "224.168.2.8")
        self.port = int(config.get("seismic_port", 42112))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)

    def send(self, method, **data):
        try:
            self.sock.sendto(
                    json.dumps([
                        time.time(),
                        config["site_name"],
                        config["host"],
                        method,
                        data
                        ]),
                    (self.addr, self.port))
        except:
            log_traceback(handlers=False)

messaging = Messaging()

##
# Logging
##

def seismic_log(**kwargs):
    messaging.send("log", **kwargs)

logging.user = config["user"]
logging.add_handler(seismic_log)

##
# Filesystem
##

class Storage():
    def __init__(self,  **kwargs):
        self.settings = kwargs

    def __getitem__(self, key):
        return self.settings[key]

    def __repr__(self):
        return "storage ID:{} ({})".format(self.id, self["title"])

    @property
    def id(self):
        return self["id"]

    @property
    def local_path(self):
        if self["protocol"] == LOCAL:
            return self["path"]
        elif PLATFORM == "unix":
            return os.path.join("/mnt/{}_{:02d}".format(config["site_name"], self.id))
        #lif PLATFORM == "windows":
            #TODO
        #   pass
        logging.warning("Unsuported {} platform: {}".format(self, self["protocol"]))

    def __len__(self):
        return ismount(self.local_path) and len(os.listdir(self.local_path)) != 0


class Storages():
    def __init__(self):
        self.clear()

    def clear(self):
        self.data = {}

    def add(self, storage):
        assert isinstance(storage, Storage)
        self.data[storage.id] = storage

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return self.data.__iter__()


storages  = Storages()
