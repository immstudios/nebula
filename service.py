#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nebula import *


class BaseService(object):
    def __init__(self, id_service, settings=False):
        logging.debug("Initializing service")
        self.id_service = id_service
        self.settings   = settings

        try:
            self.on_init()
        except SystemExit:
            pass
        except:
            logging.error("Unable to initialize service: {}".format(traceback.format_exc()))
            self.shutdown()
        else:
            db = DB()
            db.query("UPDATE nx_services SET last_seen = %d, state=1 WHERE id_service=%d" % (time.time(), self.id_service))
            db.commit()
        logging.goodnews("Service started")

    def on_init(self):
        pass

    def on_main(self):
        pass

    def soft_stop(self):
        logging.info("Soft stop requested")
        db = DB()
        db.query("UPDATE nx_services SET state=3 WHERE id_service=%d"%self.id_service)
        db.commit()

    def shutdown(self, no_restart=False):
        logging.info("Shutting down")
        if no_restart:
            db = DB()
            db.query("UPDATE nx_services SET autostart=0 WHERE id_service=%s", [self.id_service])
            db.commit()
        sys.exit(0)

    def heartbeat(self):
        db = DB()
        db.query("SELECT state FROM nx_services WHERE id_service=%s" % self.id_service)
        try:
            state = db.fetchall()[0][0]
        except:
            state = KILL
        else:
            db.query("UPDATE nx_services SET last_seen = %d, state=1 WHERE id_service=%d" % (time.time(), self.id_service))
            db.commit()

        if state in [STOPPED, STOPPING, KILL]:
            self.shutdown()



if __name__ == "__main__":
    try:
        id_service = int(sys.argv[1])
    except:
        critical_error("You must provide service id as first parameter")

    db = DB()
    db.query("SELECT agent, title, host, loop_delay, settings FROM nx_services WHERE id_service=%d" % id_service)
    try:
        agent, title, host, loop_delay, settings = db.fetchall()[0]
    except:
        critical_error("Unable to start service %s. No such service" % id_service)

    config["user"] = title

    if host != HOSTNAME:
        critical_error("This service should not run here.")

    if settings:
        try:
            settings = ET.XML(settings)
        except:
            db.query("UPDATE nx_services SET autostart=0 WHERE id_service=%d" % id_service)
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
