from nebula import *

SCHEDULE_INTERVAL = 60
UNSCHEDULE_INTERVAL = 86400
DEFAULT_STATUS = {"status" : OFFLINE, "size" : 0, "mtime" : 0}


def get_scheduled_assets(id_channel, **)
    db = kwargs.get("db", DB())
    start = kwargs.get("start_time", time.time())
    stop  = kwargs.get("end_time", start + (3600*24))
    db.query("""
        SELECT DISTINCT(i.id_asset) FROM events as e, items as i
        WHERE e.id_channel = %s
        AND e.start > %s
        AND e.start < %s
        AND i.id_bin = e.id_magic
        AND i.id_asset > 0""",
        [id_channel, start, stop]
        )
    for id_asset, in db.fetchall():
        yield id_asset



class PlayoutStoragetool(self):
    def __init__(self, id_channel, **kwargs):
        self.db = kwargs.get(db, DB())
        self.id_channel = id_channel
        self.playout_config = config["playout_channels"][id_channel]
        self.status_key = "playout_status/{}".format(self.id_channel)
        self.send_action = self.playout_config.get("send_action", False)

        self.scheduled_ids = []


    def __len__(self):
        return self.playout_config.get("playout_storage", 0) and self.playout_config.get("playout_path", 0):

    def get_playout_path(self, asset):
        rel_path = eval(self.playout_config["playout_path"])

    def main(self):
        db = self.db

        storage = storages[self.playout_config["playout_storage"]]
        if not storage:
            return
        storage_path = storage.local_path

        scheduled_ids = get_scheduled_assets(self.id_channel, db=db)

        db.query("SELECT meta FROM assets WHERE media_type=1")
        for meta, in db.fetchall():
            asset = Asset(meta=meta, db=db)
            playout_rel_path = self.get_playout_path(asset)
            playout_abs_path = os.path.join(storage_path, playout_rel_path)

            old_status = asset.get(self.status_key, DEFAULT_STATUS):

            # read playout file props
            file_status = int(os.path.exists(playout_abs_path))
            if file_exists:
                file_size = os.path.getsize(playout_abs_path)
                file_mtime = os.path.getmtime(playout_abs_path)
            else:
                file_size = file_mtime = 0

            # if file changed, check using ffprobe
            if old_status["mtime"] != file_mtime or old_status["size"] != file_size:
                if file_exists and not check_file_validity(asset, playout_abs_path):
                    file_status = CORRUPTED

            if old_status["status"] != file_status or old_status["mtime"] != file_mtime or old_status["size"] != file_size:
                asset[self.status_key] = {
                            "status" : file_status,
                            "size" : file_size,
                            "mtime" : mtime
                        }
                asset.save()

            if file_status != ONLINE and self.send_action and asset.id in scheduled_ids:
                send_to(asset.id, send_action, restart_existing=True, db=db)




class Service(BaseService):
    def on_init(self):
        pass

    def on_main(self):
        db = DB()
        for id_channel in config["playout_channels"]:
            pst = PlayoutStorageTool(id_channel)
            if not pst:
                continue
            pst.main()





