#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys

##
# Env setup
##

if sys.version_info[:2] < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

nebula_root = os.path.abspath(os.path.split(sys.argv[0])[0])

##
# Vendor imports
##

vendor_dir = os.path.join(nebula_root, "vendor")
if os.path.exists(vendor_dir):
    for pname in os.listdir(vendor_dir):
        pname = os.path.join(vendor_dir, pname)
        pname = os.path.abspath(pname)
        if not pname in sys.path:
            sys.path.insert(0, pname)

from nx import *
from nx.plugins import plugin_path

config["nebula_root"] = nebula_root


if plugin_path:
    python_plugin_path = os.path.join(plugin_path, "python")
    if os.path.exists(python_plugin_path):
        sys.path.append(python_plugin_path)


if __name__ == "__main__":
    try:
        id_service = int(sys.argv[1])
    except:
        critical_error("You must provide service id as first parameter")

    db = DB()
    db.query("SELECT agent, title, host, loop_delay, settings FROM services WHERE id=%s", [id_service])
    try:
        agent, title, host, loop_delay, settings = db.fetchall()[0]
    except:
        critical_error("Unable to start non-existing service {}".format(service))

    config["user"] = logging.user = title

    if host != config["host"]:
        critical_error("This service should not run here.")

    if settings:
        try:
            settings = ET.XML(settings)
        except:
            db.query("UPDATE services SET autostart=0 WHERE id=%s", [id_service])
            db.commit()
            critical_error("Malformed settings XML")


    _module = __import__("services.%s" % agent, globals(), locals(), ["Service"], -1)
    Service = _module.Service

    service = Service(id_service, settings)

    while True:
        try:
            service.on_main()
            last_run = time.time()
            while True:
                time.sleep(min(loop_delay, 2))
                service.heartbeat()
                if time.time() - last_run >= loop_delay:
                    break
        except (KeyboardInterrupt):
            sys.exit(0)
        except (SystemExit):
            break
        except:
            log_traceback()
            time.sleep(2)
            sys.exit(1)

