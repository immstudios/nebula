import os
import imp

from .common import *

def t(*args):
    tools_dir = os.path.join(plugin_path, "tools")
    plugin_name = args[0]

    try:
        fp, pathname, description = imp.find_module(plugin_name, [tools_dir])
    except ImportError:
        critical_error ("unable to locate module: " + plugin_name)

    try:
        module = imp.load_module(plugin_name, fp, pathname, description)
    except Exception as e:
        print (e)
