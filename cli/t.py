import imp

from nxtools import logging, log_traceback, critical_error
from nx.plugins import get_plugin_path


def t(*args):
    tools_dir = get_plugin_path("tools")
    if not tools_dir:
        return
    plugin_name = args[0]

    try:
        fp, pathname, description = imp.find_module(plugin_name, [tools_dir])
    except ImportError:
        critical_error("unable to locate module: " + plugin_name)

    try:
        module = imp.load_module(plugin_name, fp, pathname, description)
    except Exception:
        log_traceback()
        critical_error("Unable ot open tool " + plugin_name)

    logging.user = plugin_name
    margs = args[1:] if len(args) > 1 else []
    module.Plugin(*margs)
