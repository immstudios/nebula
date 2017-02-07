import os
import imp

from nebula import *

class PlayoutPlugins(object):
    def __init__(self, channel):
        self.plugins = []
        if not plugin_path:
            return
        bpath = os.path.join(plugin_path, "playout")
        if not os.path.exists(bpath):
            logging.warning("Playout plugins directory does not exist")
            return

        for fname in os.listdir(bpath):
            mod_name, file_ext = os.path.splitext(fname)
            if file_ext != ".py":
                continue

            if not mod_name in channel.enabled_plugins:
                continue

            try:
                py_mod = imp.load_source(mod_name, os.path.join(bpath, fname))
            except:
                log_traceback("Unable to load plugin {}".format(mod_name))
                continue

            if not "__manifest__" in dir(py_mod):
                logging.warning("No plugin manifest found in {}".format(fname))
                continue

            if not "Plugin" in dir(py_mod):
                logging.warning("No plugin class found in {}".format(fname))

            logging.info("Initializing plugin {} on channel {}".format(py_mod.__manifest__["name"], channel.ident ))
            self.plugins.append(py_mod.Plugin(channel))
            self.plugins[-1].title = py_mod.__manifest__["name"]

    def __getitem__(self, key):
        return self.plugins[key]


