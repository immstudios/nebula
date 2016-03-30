#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    This file is part of Nebula media asset management.
#
#    Nebula is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Nebula is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function

import os
import sys

#
# Env setup
#

if sys.version_info[:2] < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

nebula_root = os.path.abspath(os.getcwd())

#
# Vendor imports
#

vendor_dir = os.path.join(nebula_root, "vendor")
if os.path.exists(vendor_dir):
    for pname in os.listdir(vendor_dir):
        pname = os.path.join(vendor_dir, pname)
        pname = os.path.abspath(pname)
        if not pname in sys.path:
            sys.path.insert(0, pname)

from nx import *
config["nebula_root"] = nebula_root

#
# Start agents only if this script is executed (not imported)
#

if __name__ == "__main__":

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
        logging.info("Shutting down agents")
        for agent in agents:
            agent.shutdown()
        while are_running(agents):
            time.sleep(.5)

    agents = []

    for Agent in [StorageMonitor, ServiceMonitor, SystemMonitor]:
        try:
            agents.append(Agent())
        except:
            log_traceback()
            shutdown(agents)
            critical_error("Unable to start {}".format(Agent.__name__))

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    print()
    try:
        logging.warning("Shutting down nebula. Please wait...")
        shutdown(agents)
        logging.goodnews("Exiting gracefully")
        sys.exit(0)
    except KeyboardInterrupt:
        logging.warning("Immediate shutdown enforced. This may cause problems")
        sys.exit(1)
