import os
import imp

from nx import *
from nx.services import BaseService
from nx.plugins import plugin_path

class Service(BaseService):
    def on_init(self):
        self.exec_init = False
        self.exec_main = False
        self.plugin = False

        if "script" in self.settings.attrib:
            fname = self.settings.attrib["script"]
            result = self.load_from_scipt(fname)
        else:
            result = self.load_from_settings()

        if not result:
            logging.error("Unable to load worker. Shutting down")
            self.shutdown(no_restart=True)


    def load_from_scipt(self, fname):
        script_path = os.path.join(plugin_path, "worker", fname)
        mod_name, file_ext = os.path.splitext(fname)

        if not os.path.exists(script_path):
            logging.error("Plugin {} not found".format(fname))
            return False

        py_mod = imp.load_source(mod_name, script_path)

        if not "Plugin" in dir(py_mod):
            logging.error("No plugin class found in {}".format(fname))
            return False

        logging.debug("Loading plugin {}".format(mod_name))
        self.plugin = py_mod.Plugin(self)
        self.plugin.on_init()
        return True


    def load_from_settings(self):
        try:
            self.exec_init = self.settings.find("init").text
        except:
            pass
        try:
            self.exec_main = self.settings.find("main").text
        except:
            pass

        if self.exec_init:
            exec (self.exec_init)

        return True



    def on_main(self):
        if self.plugin:
            self.plugin.on_main()

        elif self.exec_main:
            exec (self.exec_main)

