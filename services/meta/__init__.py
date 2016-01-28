from nx import *
from nx.services import BaseService
from nx.objects import Asset
from nx.core.metadata import meta_types

from probes import probes


class Service(BaseService):
    def on_init(self):
        filters = [] # Ignore archived and trashed
        #filters.append("status=%d"%CREATING)
        if filters:
            self.filters = "AND " + " AND ".join(filters)
        else:
            self.filters = ""

    def on_main(self):
        self.mounted_storages = []
        for id_storage in storages:
            sp = storages[id_storage].local_path
            if os.path.exists(sp) and len(os.listdir(sp)) != 0:
                self.mounted_storages.append(id_storage)

        db = DB()
        db.query("SELECT id_object FROM nx_assets WHERE media_type = 0 {} AND status NOT IN (3,4)".format(self.filters))
        for id_asset, in db.fetchall():
            self._proc(id_asset, db)

    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        fname = asset.file_path

        if asset["id_storage"] not in self.mounted_storages:
            return

        if not os.path.exists(fname):
            if asset["status"] in [ONLINE, RESET, CREATING]:
                logging.warning("Turning offline {} (File does not exist)".format(asset))
                asset["status"] = OFFLINE
                asset.save()
            return

        try:
            fmtime = int(os.path.getmtime(fname))
            fsize  = int(os.path.getsize(fname))
        except:
            self.logging.error("Strange error 0x001 on %s" % asset)
            return

        if fsize == 0:
            if asset["status"] != OFFLINE:
                logging.warning("Turning offline {} (empty file)".format(asset))
                asset["status"] = OFFLINE
                asset.save()
            return

        if fmtime != asset["file/mtime"] or asset["status"] == RESET:
            try:
                f = open(fname,"rb")
            except:
                logging.debug("{} creation in progress.".format(asset))
                return
            else:
                f.seek(0,2)
                fsize = f.tell()
                f.close()

            if asset["status"] == RESET:
                asset.load_sidecar_metadata()

            # Filesize must be changed to update metadata automatically.
            # It sucks, but mtime only condition is.... errr doesn't work always

            if fsize == asset["file/size"] and asset["status"] != RESET:
                logging.debug("{} file mtime has been changed. Updating.".format(asset))
                asset["file/mtime"] = fmtime
                asset.save(set_mtime=False, notify=False)
            else:
                logging.info("Updating {}".format(asset))

                keys = list(asset.meta.keys())
                for key in keys:
                    if meta_types[key].namespace in ("fmt", "qc"):
                        del (asset.meta[key])

                asset["file/size"]  = fsize
                asset["file/mtime"] = fmtime

                #########################################
                ## PROBE

                for probe in probes:
                    if probe.accepts(asset):
                        logging.debug("Probing {} using {}".format(asset, probe))
                        asset = probe.work(asset)

                ## PROBE
                #########################################

                if asset["status"] == RESET:
                    asset["status"] = ONLINE
                    logging.info("{} reset completed".format(asset))
                else:
                    asset["status"] = CREATING
                asset.save()


        if asset["status"] == CREATING and asset["mtime"] + 15 > time.time():
            logging.debug("Waiting for {} completion assurance.".format(asset))
            asset.save(set_mtime=False, notify=False)

        elif asset["status"] in (CREATING, OFFLINE):
            logging.goodnews("Turning online {}".format(asset))
            asset["status"] = ONLINE
            asset.save()

            db = DB()
            db.query("""UPDATE nx_jobs SET progress=-1, id_service=0, ctime=%s, stime=0, etime=0, id_user=0, message='Restarting after source update'
                    WHERE id_object=%s AND id_action > 0 and progress IN (-2, -3)""",
                    [time.time(), id_asset]
                    )

            db.commit()
