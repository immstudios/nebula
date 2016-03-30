from nx import *
from nx.services import BaseService
from nx.objects import Asset
from nx.jobs import send_to

class Service(BaseService):
    def on_init(self):
        self.conditions = {}
        db = DB()
        db.query("SELECT id, title, settings FROM actions")
        for id_action, title, aconfig in db.fetchall():
            try:
                start_cond = ET.XML(aconfig).find("start_if")
            except:
                logging.debug("No start condition for action {}".format(title))
                continue

            try:
                priority = int(start_cond.attrib["priority"])
            except:
                priority = 1

            if start_cond is not None and start_cond.text:
                logging.debug("Initializing broker condition for {}".format(title))
                self.conditions[id_action] = (title, start_cond.text, priority)


    def on_main(self):
        db = DB()
        db.query("SELECT id FROM assets WHERE status=%s", [ONLINE])
        for id_asset, in db.fetchall():
            self._proc(id_asset, db)


    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        for id_action in self.conditions:
            if "broker/started/{}".format(id_action) in asset.meta:
                continue
            cond_title, cond, priority = self.conditions[id_action]
            if eval(cond):
                logging.info("{} matches action condition {}".format(asset, cond_title))
                res, msg = send_to(asset.id, id_action, settings={}, id_user=0, priority=priority, restart_existing=False, db=db)

                if success(res):
                    logging.info(msg)
                else:
                    logging.error(msg)

                asset["broker/started/{}".format(id_action)] = 1
                asset.save()



