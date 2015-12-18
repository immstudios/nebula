#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# To my future self: keep this simple, please.
#

from __future__ import print_function

import os
import sys

print ("")

if sys.version_info[:2] < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

##
# Vendor imports
##

if os.path.exists("vendor"):
    for pname in os.listdir("vendor"):
        pname = os.path.join("vendor", pname)
        pname = os.path.abspath(pname)
        if not pname in sys.path:
            sys.path.append(pname)
    
from nx import *

##
# Start agents only if this script is executed (not imported)
##

if __name__ == "__main__":

    from admin import Admin
    from nx.storage_monitor import StorageMonitor
    from nx.service_monitor import ServiceMonitor
    from nx.system_monitor import SystemMonitor

    def are_running(agents):
        for agent in agents:
            if agent.is_running:
                break
        else:
            return False
        return True

    def shutdown(agents):
        logging.warning("Shutting down agents")
        for agent in agents:
            agent.shutdown()
        while are_running(agents):
            time.sleep(.5)

    agents = []

    for agent in [Admin, StorageMonitor, ServiceMonitor, SystemMonitor]:
        try:
            agents.append(agent())
        except:
            log_traceback()
            shutdown(agents)
            critical_error("Unable to start Nebula")

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.warning("Shutting down nebula. Please wait...")
            shutdown(agents)
            logging.goodnews("Exiting gracefully")
            sys.exit(0)
