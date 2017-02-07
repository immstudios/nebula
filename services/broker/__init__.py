from nebula import *

class Action(object):
    def __init__(self, id, title, settings):
            self.id = id
            self.start_if = self.find("start_if")

            if self.start_if is not None:
                if self.start_if.text:
                    logging.debug("Initializing broker condition for {}".format(title))
                    self.start_if = self.start_if.text
                else:
                    self.start_if = None

    @property
    def started_key(self):
        return "job_started/{}".format(self.id)

    def should_start(self, asset):
        return eval(self.start_if)


class Service(BaseService):
    def on_init(self):
        self.actions = []
        db = DB()
        db.query("SELECT id, title, settings FROM actions")
        for id, title, settings in db.fetchall():
            self.settings = xml(settings)
            self.actions.append([id, title, settings])

    def on_main(self):
        db = DB()
        db.query("SELECT id, meta FROM assets WHERE status=%s", [ONLINE])
        for id_asset, meta in db.fetchall():
            asset = Asset(meta=meta, db=db)
            self.proc(asset)


    def proc(self, asset):
        for action in self.actions:
            if action.started_key in asset.meta:
                continue

            if action.should_start(asset):
                logging.info("{} matches action condition {}".format(asset, cond_title))
                res, msg = send_to(
                        asset.id,
                        action.id,
                        settings={},
                        id_user=0,
                        restart_existing=False,
                        db=db
                    )

                if success(res):
                    logging.info(msg)
                else:
                    logging.error(msg)

                asset[action.started_key] = 1
                asset.save()
