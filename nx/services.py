#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback

from nx.common import *
from nx.connection import *

class ServicePrototype(object):
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

__all__ = ["ServicePrototype"]
