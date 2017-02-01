from .common import *
from .constants import *

class CSItem(object):
    def __init__(self, key, value, **settings):
        self.key = key
        self.value = value
        self.settings = settings

    def __getitem__(self, key):
        return self.settings[key]


class CSList(object):
    def __init__(self, name):
        self.name = name

    def __iter__(self):
        return [CSItem(key, value, **settings) for key, value, settings in config["cs"][self.name]]

    def __getitem__(self, key):
        data = config["cs"][self.name][key]
        return CSItem(key[0], key[1], **key[2])


class CS(object):
    def __getitem__(self, key):
        return CSList(key, config["cs"][key])

cs = CS()
