#!/usr/bin/env python
#
#    This file is part of Nebula media asset management.
#
#    Nebula is` free software: you can redistribute it and/or modify
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
#    along with Nebula. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function

import os
import sys

from nebula import *

logging.user = "Manager"

#
# Service / admin runner
#

def run(*args):
    id_service = args[0]

    if id_service == "hub":
        import hub
        try:
            hub_instance = hub.CherryAdmin(**hub.hub_config)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            log_traceback()
            critical_error("Unhandled exception in Hub")
        sys.exit(0)

    try:
        id_service = int(id_service)
    except ValueError:
        critical_error("Service ID must be integer")

    db = DB()
    db.query("SELECT service_type, title, host, loop_delay, settings FROM services WHERE id=%s", [id_service])
    try:
        agent, title, host, loop_delay, settings = db.fetchall()[0]
    except IndexError:
        critical_error("Unable to start service {}. No such service".format(id_service))

    config["user"] = logging.user = title

    if host != config["host"]:
        critical_error("This service should not run here.")

    if settings:
        try:
            settings = xml(settings)
        except Exception:
            log_traceback()
            logging.error("Malformed settings XML:\n", settings)
            db.query("UPDATE services SET autostart=0 WHERE id=%s", [id_service])
            db.commit()
            critical_error("Unable to start service")

    _module = __import__("services." + agent, globals(), locals(), ["Service"], -1)
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

#
# Administration
#

def add_user(*args):
    print ()
    try:
        login = raw_input("Login: ").strip()
        password = raw_input("Password: ").strip()
        is_admin = raw_input("Is it admin (yes/no): ").strip()
    except KeyboardInterrupt:
        print()
        logging.warning("Interrupted by user")
        sys.exit(0)
    u = User()
    u["login"] = u["full_name"] = login
    u["is_admin"] = 1 if is_admin == "yes" else 0
    u.set_password(password)
    u.save()
    print()
    logging.goodnews("User created")




if __name__ == "__main__":
    methods = {
            "run" : run,
            "adduser" : add_user
        }

    if len(sys.argv) < 2:
        critical_error("This command takes at least one argument")
    method = sys.argv[1]
    args = sys.argv[2:]
    if not method in methods:
        critical_error("Unknown method '{}'".format(method))
    methods[method](*args)
